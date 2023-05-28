"""Processes config file and manages houclip configuration."""

import configparser
import csv
import os
import tempfile
from pathlib import Path
from .broadcast import Broadcast
from .menu import Menu, MENUS
from . import messages


PREFIXES = {
    'Chop': 'CHOP',
    'ChopNet': 'CHOPNET',
    'Cop2': 'COP2',
    'CopNet': 'IMG',
    'Director': None,
    'Dop': 'DOP',
    'Driver': 'ROP',
    'Lop': 'LOP',
    'Manager': None,
    'Object': 'OBJ',
    'Shop': 'SHOP',
    'Sop': 'SOP',
    'Top': 'TOP',
    'TopNet': 'TOPNET',
    'Vop': 'VOP',
    'VopNet': None,
}
"""dict: Keys of `PREFIXES` dictionary are Houdini node type category names.

`PREFIXES` keys are derived from:

``sorted(list(hou.nodeTypeCategories().keys()))``

In Houdini, whenever a selection of nodes is copied to clipboard,
a ``.cpio`` file with a corresponding prefix (specific to type category)
is created in ``$HOUDINI_TEMP`` path.
The prefix is always upper-cased and may, or may not be an operator's
type category name (e.g. Sop:SOP, but Driver:ROP). This dictionary
translates type category names into those prefixes.

Some prefixes are set to None and the reason is that some node type
categories are no longer in use (as is in the case of VopNet), or copying
them using manual UI clipboard actions is not possible (``Director``
and ``Manager`` nodes).

Type category --- prefix relation is hardcoded in order to avoid situations,
in which this module stops working correctly, because a new category is added
in a consecutive Houdini version.

"""

CATEGORIES = tuple(PREFIXES)
"""tuple: Contains keys of `PREFIXES` dictionary. For code clarity."""

LANGUAGES = ('HScript', 'Python', 'VEX')
"""tuple: List of snippet programming languages supported by the program.

No dictionary is required, because these are not Houdini node type
categories.

"""


class Config:
    """Manage program's configuration.

    Singleton convenience class that makes creating, accessing
    and managing program's configuration easier than it would otherwise
    be with purely procedural programming.

    Configuration file is always looked up in:

    ``$HOUDINI_USER_PREF_DIR/packages/houclip/houclip.conf``

    If the configuration file isn't found, it will be created when
    the `Config` instance is created and the file will be filled
    with default, hardcoded values.

    During object construction, a validation of repository hierarchy
    is performed where the class checks if this path exists, and if not,
    creates it based on module's tuple of `CATEGORIES` and `LANGUAGES`.
    Default repository location is in:

    ``$HOME/.local/share/houclip``

    Attributes:
        __instance (Config): Stores information about class instances.
        __package_path (Path):
            Stores information about ``houclip`` package location.
        __path (Path):
            Path to ``houclip.conf`` (derived from `__package_path`).
        __repo (Path): Path to ``houclip`` snippets repository.
        __delimiter (str): CSV delimiting character.
        __dialect (str): CSV dialect.
        __quoting (int): Character used to quote special characters in CSV.
        __menu (str): Which menu to use.
        __theme (str): Menu theme.
        __max_desc_len (int):
            Maximum length of description string (used in string formatting
            for ``dmenu``).
        __max_tags_len (int):
            Maximum length of tags string (used in string formatting
            for ``dmenu``).

    """

    __instance = None
    __package_path = Path(
        Path(os.path.realpath(__file__)).parents[3])
    __path = Path(__package_path, 'houclip.conf')
    __DEFAULT_PATHS = {
        'repo': os.path.expandvars('$HOME/.local/share/houclip')
    }
    """dict: Hardcoded defaults for the ``PATHS`` section of
    the config file."""
    __DEFAULT_CSV = {
        'delimiter': ';',
        'dialect': 'unix',
        'quoting': csv.QUOTE_MINIMAL
    }
    """dict: Hardcoded defaults for the ``CSV`` section of the config file."""
    __DEFAULT_MENU = {
        'menu': 'Dmenu',
        'theme': '',
        'max_desc_len': 128,
        'max_tags_len': 32
    }
    """dict: Hardcoded defaults for the ``MENU`` section of
    the config file."""

    def __new__(cls):
        """Create Config object.

        Implements basic singleton pattern.

        Returns:
            Config:
                Returns existing `Config` object, or its new instance
                if it wasn't created yet.

        """
        if cls.__instance is None:
            cls.__instance = super(Config, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        """Initialize the object."""
        parser = configparser.ConfigParser()
        # Create default config file if the config file doesn't exist.
        if not self.__path.exists():
            parser['PATHS'] = self.__DEFAULT_PATHS
            parser['CSV'] = self.__DEFAULT_CSV
            parser['MENU'] = self.__DEFAULT_MENU
            with open(Config.__path, 'w', encoding='utf-8') as config_file:
                parser.write(config_file)
        # Read config file into attributes.
        parser.read(Config.__path)
        self.__repo = Path(self.__get_key('repo', 'PATHS'))
        self.__delimiter = self.__get_key('delimiter', 'CSV')
        self.__dialect = self.__get_key('dialect', 'CSV')
        self.__quoting = int(self.__get_key('quoting', 'CSV'))
        self.__menu = MENUS[self.__get_key('menu', 'MENU').capitalize()]
        self.__theme = self.__get_key('theme', 'MENU')
        self.__max_desc_len = int(self.__get_key('max_desc_len',
                                                 'MENU'))
        self.__max_tags_len = int(self.__get_key('max_tags_len',
                                                 'MENU'))
        self.__validate_hierarchy()

    def __get_key(self, key: str, section: str) -> str:
        """Retrieve a key from specific section of the config file.

            Used only on `Config` object creation.

        Args:
            key (str): Configuration key to look up.
            section (str): Configuration section to be queried.

        Returns:
            str: Key value.

        Raises:
            ValueError: Config key was not found.

        """
        parser = configparser.ConfigParser()
        parser.read(Config.__path)
        if parser.has_option(section, key):
            return parser[section][key]
        raise ValueError('Config key not found.')

    def __validate_hierarchy(self) -> None:
        """Check if repository exists. If required, recreate its hierarchy."""
        if not self.__repo.exists():
            self.__repo.mkdir(parents=True)
        for category in (CATEGORIES + LANGUAGES):
            directory = Path(self.__repo, category)
            if not directory.exists():
                Broadcast.stdout(f'{messages.MKDIR} {directory}', 0)
                directory.mkdir()
            list_file = Path(self.__repo, f'{category}.csv')
            if not list_file.exists():
                Broadcast.stdout(f'{messages.TOUCH} {list_file}', 0)
                list_file.touch()

    @staticmethod
    def houdini_temp() -> Path:
        """Return path to Houdini temporary directory.

           Returns:
                Path: Path to Houdini temporary directory.

        """
        houdini_temp = os.getenv('HOUDINI_TEMP')
        if houdini_temp is None:
            return Path(tempfile.gettempdir(), 'houdini_temp')
        return houdini_temp

    @classmethod
    def package_path(cls) -> Path:
        """Return houclip's package path."""
        return cls.__package_path

    @property
    def repo(self) -> str:
        """Return path to snippets repository."""
        return self.__repo

    @property
    def delimiter(self) -> str:
        """Return CSV delimiting character."""
        return self.__delimiter

    @property
    def dialect(self) -> str:
        """Return CSV dialect."""
        return self.__dialect

    @property
    def quoting(self) -> int:
        """Return quoting character used by CSV parser for special chars."""
        return self.__quoting

    @property
    def menu(self) -> Menu:
        """Return UI."""
        return self.__menu

    @property
    def theme(self) -> str:
        """Return menu theme, if any."""
        return self.__theme

    @property
    def max_desc_len(self) -> int:
        """Return the maximum length of snippet's description string."""
        return self.__max_desc_len

    @property
    def max_tags_len(self) -> int:
        """Return the maximum length of snippet's tags string."""
        return self.__max_tags_len
