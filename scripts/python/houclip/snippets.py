"""Defines and manages houclip snippets.

This module helps in maintaining a repository of Houdini network snippets,
as well as text snippets collected from anywhere in the operating system.

Typical usage (Houdini):

    ``houclip.main(houdini=True)``

Typical usage (shell):

    ``houclip.main()``

"""

import csv
import gzip
import os
import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid1
from .config import Config, CATEGORIES, LANGUAGES, PREFIXES
from . import messages
from .broadcast import Broadcast
from .clipboard import Clipboard


assert ('linux' in sys.platform), messages.GNU_LINUX


class Snippet(ABC):
    """Abstract base class for all snippet-type objects.

    Attributes:
        __config (Config): Reference to `Config` instance.
        instances (list[Snippet]): List of class instances.
        description (str): Snippet description.
        tags (list[str]): List of tags.
        category (str): Houdini node type category name.
        uuid (str): hexadecimal representation of UUID1.

    """

    __instances = []
    __config = Config()

    def __init__(self, **kwargs):
        """Construct Snippet object.

        Args:
            **kwargs:
                Keyword arguments are used in attribute assignment.
                Available keys are: ``description (str)``, ``tags (str)``,
                ``category (str)``, ``prefix (str)``, and ``uuid (str)``.

        """
        self.description = kwargs['description']
        self.tags = kwargs['tags']
        self.category = kwargs['category']
        self.prefix = kwargs['prefix']
        self.uuid = kwargs['uuid']
        Snippet.__instances.append(self)

    def __str__(self):
        """Return object as string.

        Formats the string by truncating the `Snippet.description` to
        `Config.max_desc_len` and separating it from `Snippet.tags`
        (truncated to `Config.max_tags_len`) with ``|`` character.

        Returns:
            str: Formatted string.

        """
        config = Config()
        desc_len = config.max_desc_len
        desc = self.description
        tags = ','.join(self.tags)
        space = desc_len + 2
        return f'{desc[0:desc_len]:<{space}}|{tags}'

    @abstractmethod
    def store_in_repo(self, **kwargs) -> None:
        """Store snippet in repository."""
        # Kwargs are used as a substitute for polymorphism.

    @abstractmethod
    def get_from_repo(self) -> None:
        """Retrieve snippet from repository."""

    def add_to_list(self) -> None:
        """Put information about snippet to CSV file.

        Appends CSV file (corresponding to snippet's category)
        with snippet object's data.

        """
        config = Config()
        list_file = Path(Config().repo, f'{self.category}.csv')
        tags = ','.join(self.tags)
        with open(list_file, 'a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=config.delimiter,
                                dialect=config.dialect, quoting=config.quoting)
            writer.writerow([self.description, tags, self.category,
                             self.prefix, self.uuid])

    @staticmethod
    def csv_reader(source_file: Path) -> csv.reader:
        """Returns new CSV reader for a CSV file supplied as argument.

        Args:
            source_file (Path):
                Path to CSV file containing information about the snippet.

        Returns:
            csv.reader:
                New CSV reader with loaded CSV file containing information
                about the snippet.

        """
        config = Config()
        reader = csv.reader(source_file, delimiter=config.delimiter,
                            dialect=config.dialect, quoting=config.quoting)
        return reader

    @staticmethod
    def csv_writer(target_file: Path) -> csv.writer:
        """Returns new CSV writer for file supplied as argument.

        Args:
            target_file (Path):
                Path to CSV file containing information about the snippet.

        Returns:
            csv.writer:
                New CSV writer with loaded CSV file containing information
                about the snippet.

        """
        config = Config()
        writer = csv.writer(target_file, delimiter=config.delimiter,
                            dialect=config.dialect, quoting=config.quoting)
        return writer

    @classmethod
    def purge(cls) -> None:
        """Remove all class instances."""
        cls.__instances = []

    @classmethod
    def instances(cls) -> list:
        """Return `Snippet` instances."""
        return cls.__instances

    @classmethod
    def instances_as_str(cls) -> str:
        """Return string representations of all instances.

        Returns:
            str:
                String consisting of ``__str__`` representations
                of all snippet instances, one per line.

        """
        return '\n'.join([str(instance) for instance in cls.__instances])

    @classmethod
    def get_by_description(cls, description: str) -> object:
        """Return a Snippet object which contains a specific description.

        Searches Snippet instances for specific `description`.

        Args:
            description (str): Description to search for.

        Returns:
            Snippet: Snippet instance with a matching `description` attribute.

        """
        for instance in cls.__instances:
            if instance.description == description:
                return instance
        return None

    def delete(self) -> None:
        """Remove snippet from repository.

        Performs snippet removal by:

        - removing information about it from its corresponding CSV file,
        - removing its data file,
        - removing the object from `Snippet` instances.

        Raises:
            FileNotFoundError:
                CSV file containing information about the Snippet
                was not found.

        """
        config = Config()
        list_file_path = Path(config.repo, f'{self.category}.csv')
        if os.stat(list_file_path).st_size == 0:
            Broadcast.all(f'{messages.CSV_EMPTY} {list_file_path}', 4)
        temp_file = Path(f'/dev/shm/houclip_{uuid1().hex}.csv')
        if not list_file_path.exists():
            raise FileNotFoundError(f'{messages.CSV_MISSING}')
        with (
                open(list_file_path, 'r', encoding='utf-8') as input_,
                open(temp_file, 'w', encoding='utf-8') as output,
        ):
            reader = Snippet.csv_reader(input_)
            writer = Snippet.csv_writer(output)
            for row in reader:
                uuid_row = 4
                if not row[uuid_row] == self.uuid:
                    writer.writerow([row[0], row[1], row[2], row[3], row[4]])
        shutil.copyfile(temp_file, list_file_path)
        snippet_file = Path(config.repo, self.category, self.uuid)
        snippet_file.unlink()
        temp_file.unlink()
        if self in Snippet.__instances:
            Snippet.__instances.remove(self)

    @property
    def description(self) -> str:
        """Return snippet's description."""
        return self.__description

    @description.setter
    def description(self, description: str):
        """Validate and set snippet description."""
        if description == '' or description is None:
            raise ValueError(messages.DESC_REQ)
        self.__description = description

    @property
    def tags(self) -> list[str]:
        """Return snippet's tags."""
        return self.__tags

    @tags.setter
    def tags(self, tags: str):
        """Set snippet tags.

        Takes a comma-separated string, remove whitespaces, and converts it
        to a sorted list using list comprehension.

        Args:
            tags: String of comma-separated tags.
        """
        self.__tags = sorted([tag.strip() for tag in tags.split(',')])

    @property
    @abstractmethod
    def category(self) -> str:
        """Return category of the snippet."""

    @category.setter
    @abstractmethod
    def category(self, category: str):
        """Set category of the snippet."""

    @property
    def prefix(self) -> str:
        """Return clipboard prefix."""
        return self.__prefix

    @prefix.setter
    def prefix(self, prefix):
        """Set prefix.

        Args:
            prefix (str): New `prefix` of the snippet.

        Raises:
            ValueError: Prefix was not found in `PREFIXES`.

        """
        if prefix not in PREFIXES.values() and prefix is not None:
            raise ValueError(f'{messages.PREFIX_INVALID} "{prefix}".')
        if prefix is None:
            self.__prefix = ''
        else:
            self.__prefix = prefix

    @property
    def uuid(self) -> str:
        """Return UUID of the snippet, which is also its file name."""
        return self.__uuid

    @uuid.setter
    def uuid(self, uuid):
        """Set UUID of the snipet.

        Args:
            uuid (str): Hexadecimal representation of `uuid.uuid1()`.

        """
        if not isinstance(uuid, str):
            uuid = uuid.hex
        self.__uuid = uuid


class OpSnippet(Snippet):
    """Implementation of Snippet class for Houdini operator snippets."""

    @staticmethod
    def is_selection_valid(selection: list) -> bool:
        """Check if type category of the the first node is in `CATEGORIES`.

        Requires hou module.

        Args:
            selection (list[hou.NetworkMovableItem]):
                List of items selected in Network Editor.

        Returns:
            bool:
                ``True`` if all objects are of known categories. ``False``
                in other case.

        Raises:
            TypeCategoryNotFoundError:
                First `hou.NetworkItemType.Node` object in selection
                is of unknown type (not listed in `CATEGORIES`).

        """
        if len(selection) == 0:
            Broadcast.all(messages.SEL_EMPTY, 2)
            return False
        category = OpSnippet.determine_category(selection)
        if category is None:
            Broadcast.all(messages.SEL_TIP, 2)
            return False
        if category not in CATEGORIES:
            Broadcast.all(f'{messages.CAT_INVALID} {category}.', 4)
            raise TypeCategoryNotFoundError(category, selection[0].type())
        return True

    @staticmethod
    def determine_category(selection: list) -> str:
        """Find category of first ``hou.networkItemType.Node`` in selection.

        Returns node type category name of the first
        `hou.networkItemType.Node` it encounters in ``selection``.

        Requires `hou` module.

        Args:
            selection (list[hou.NetworkMovableItem]):
                List of objects selected in the Network Editor.

        Returns:
            str: Type category name of the node.

        """
        try:
            import hou
        except ModuleNotFoundError as error:
            Broadcast.all(messages.HOU_MISSING, 4)
            raise error
        category = None
        for idx, item in enumerate(selection):
            if item.networkItemType() == hou.networkItemType.Node:
                category = selection[idx].type().category().name()
                break
        return category

    def store_in_repo(self, **kwargs) -> None:
        """Store operator snippet file in repository.

        In Houdini, when a selection of operators is copied to clipboard,
        the program creates a binary file in ``$HOUDINI_TEMP`` path.
        Its file name is built from two parts: a ``prefix`` and a ``suffix``.
        It is also given has a ``.cpio`` extension.

        The prefix is a type category name of operators that are residing
        in the current context. The suffix is simply the string: ``_copy``.

        This function takes the ``.cpio`` file, compresses it with gzip
        and puts it the appropriate place in houclip repository.

        Args:
            **kwargs: Unused.

        """
        source_path = Path(Config.houdini_temp(), f'{self.prefix}_copy.cpio')
        if not source_path.exists():
            Broadcast.all(f'{messages.SOURCE_MISSING}: {source_path}', 3)
            raise FileNotFoundError(source_path)
        target_path = Path(Config().repo, self.category, self.uuid)
        with open(source_path, 'rb') as decompressed:
            with gzip.open(target_path, 'wb') as compressed:
                compressed.writelines(decompressed)

    def get_from_repo(self) -> None:
        """Fetch snippet file from repository and copy it to ``$HOUDINI_TEMP``.

        This method fetches file containing snippet contents from the houclip
        repository and unpacks it to ``$HOUDINI_TEMP``. In the process,
        it renames the file to ``{prefix}_copy.cpio``.

        """
        source_path = Path(Config().repo, self.category, self.uuid)
        target_path = Path(Config.houdini_temp(), f'{self.prefix}_copy.cpio')
        if not source_path.exists():
            Broadcast.all(f'{messages.SOURCE_MISSING}: {source_path}', 3)
            raise FileNotFoundError(source_path)
        with gzip.open(source_path, 'rb') as compressed:
            with open(target_path, 'wb') as decompressed:
                shutil.copyfileobj(compressed, decompressed)

    @property
    def category(self) -> str:
        return self.__category

    @category.setter
    def category(self, category: str):
        """Set snippet category.

        Args:
            category (str): Node type category name of the snippet.

        Raises:
            ValueError:
                Category of the `OpSnippet` object wasn't found
                in `CATEGORIES` list.

        """
        if category == '' or category not in CATEGORIES:
            raise ValueError('Empty or unknown snippet category.')
        self.__category = category


class CodeSnippet(Snippet):
    """Implementation of `Snippet` class for creating code snippets."""

    def __init__(self, **kwargs):
        kwargs['prefix'] = None
        super().__init__(**kwargs)

    def store_in_repo(self, **kwargs) -> None:
        """Copy clipboard contents to file in snippet repository.

        Args:
            **kwargs:
                The only used keyword is ``code (str)``, which should
                be string that will be saved to file.

        """
        target_path = Path(Config().repo, self.category, self.uuid)
        with open(target_path, 'w', encoding='utf-8') as target_file:
            target_file.writelines(kwargs['code'])

    def get_from_repo(self) -> None:
        """Copies contents of the snippet back to clipboard.

        Raises:
            FileNotFoundError:
                File containing the snippet was not found in the repository.

        """
        source_path = Path(Config().repo, self.category, self.uuid)
        if not source_path.exists():
            Broadcast.stdout(f'{messages.FILE_MISSING} {source_path}', 3)
            raise FileNotFoundError(source_path)
        Clipboard.fetch(str(source_path.absolute()))

    @property
    def category(self):
        return self.__category

    @category.setter
    def category(self, category: str):
        """Set snippet category.

        Args:
            category (str): Node type category of the snippet.

        Raises:
            ValueError:
                Category of the `CodeSnippet` object wasn't found
                in `LANGUAGES` list.

        """
        if category == '' or category not in LANGUAGES:
            raise ValueError('Empty or unknown language.')
        self.__category = category


class TypeCategoryNotFoundError(Exception):
    """Unknown node type category."""

    def __init__(self, category: str, operator: str):
        super().__init__(category, operator)
        self.category = category
        self.operator = operator

    def __str__(self):
        return f'"{self.category}" of node: {self.operator}.'


def add_op_snippet() -> None:
    """Collect input from user to create an `OpSnippet` object.

    This function requires `hou` module.

    """
    try:
        import hou
    except ModuleNotFoundError as error:
        Broadcast.all(messages.HOU_MISSING, 4)
        raise error
    config = Config()
    menu_kwargs = {
        'theme': config.theme,
    }
    selection = hou.selectedItems()
    if not OpSnippet.is_selection_valid(selection):
        return
    category = OpSnippet.determine_category(selection)
    prefix = f'{PREFIXES[category]}'
    selection[0].parent().copyItemsToClipboard(selection)
    description = config.menu.enter(messages.DESC, **menu_kwargs)
    if description == '' or description is None:
        Broadcast.all(messages.DESC_REQ, 2)
        return
    tags = config.menu.enter(messages.TAGS, **menu_kwargs)
    uuid = uuid1().hex
    kwargs = {
        'description': description,
        'tags': tags,
        'category': category,
        'uuid': uuid,
        'prefix': prefix,
    }
    snippet = OpSnippet(**kwargs)
    snippet.store_in_repo()
    snippet.add_to_list()
    Broadcast.all(messages.SNIPPET_ADDED, 0)


def get_snippet(categories: tuple[str] = CATEGORIES) -> None:
    """Fetch snippet from repository.

    Lets user to select a snippet which then, depending on Snippet's class,
    will be copied to either: Houdini or system clipboard.

    Args:
        categories (tuple[str], optional):
            List of categories to look up. See `CATEGORIES` and `LANGUAGES`
            for more information.

    """
    config = Config()
    menu_kwargs = {
        'theme': config.theme,
    }
    prompt = 'Which category?'
    category = (
        f'{config.menu.select(categories, prompt, **menu_kwargs).rstrip()}'
    )
    if category == '':
        return
    csv_file = Path(config.repo, f'{category}.csv')
    if not csv_file.exists():
        # Broadcast.all(f"{messages.CSV_MISSING} {csv_file}", 4)
        return
    Snippet.purge()
    with open(csv_file, 'r', encoding='utf-8') as items:
        reader = Snippet.csv_reader(items)
        for item in reader:
            kwargs = {
                'description': item[0],
                'tags': item[1],
                'category': item[2],
                'prefix': item[3],
                'uuid': item[4]
            }
            if kwargs['category'] in CATEGORIES:
                OpSnippet(**kwargs)
            else:
                CodeSnippet(**kwargs)
    snippets = [str(instance) for instance in Snippet.instances()]
    if len(snippets) == 0:
        Broadcast.all(messages.CAT_EMPTY, 0)
        return
    selected_snippet = config.menu.select(snippets, messages.SNIPPET,
                                          **menu_kwargs)
    if selected_snippet == '':
        return
    description = selected_snippet.partition('|')[0].rstrip()
    snippet = Snippet.get_by_description(description)
    snippet.get_from_repo()
    Broadcast.all(f'{snippet.category} {messages.SNIPPET_FETCHED}', 0)


def add_code_snippet() -> None:
    """Collect data required to create `CodeSnippet` object."""
    config = Config()
    menu_kwargs = {
        'theme': config.theme,
    }
    language = config.menu.select(LANGUAGES, **menu_kwargs).rstrip()
    if language not in LANGUAGES:
        Broadcast.all(f'{messages.CAT_INVALID} {language}.', 2)
        return
    description = config.menu.enter(messages.DESC, **menu_kwargs)
    if description == '' or description is None:
        return
    tags = config.menu.enter(messages.TAGS, **menu_kwargs)
    uuid = uuid1().hex
    code = Clipboard.get()
    kwargs = {
        'description': description,
        'tags': tags,
        'category': language,
        'uuid': uuid,
    }
    snippet = CodeSnippet(**kwargs)
    snippet.store_in_repo(**{'code': code})
    snippet.add_to_list()
    Broadcast.all(messages.SNIPPET_ADDED, 0)


def get_code_snippet() -> None:
    """Wrapper of `get_snippet()`, but for code snippets."""
    get_snippet(LANGUAGES)


def del_snippet(code: bool = False) -> None:
    """Remove selected `Snippet` from repository.

    Prompts user to select category and then a snippet he wants to remove.
    Then removes the snippet by calling `Snippet.delete()`.

    Args:
        code (bool, optional):
            Indicates `Snippet` subclass. If `True`, tells the function
            to operate on `CodeSnippet` object. If `False`, operation
            is performed on `OpSnippet` object.

    """
    config = Config()
    menu_kwargs = {
        'theme': config.theme,
    }
    if code:
        category = config.menu.select(LANGUAGES, messages.CAT,
                                      **menu_kwargs).strip()
    else:
        category = config.menu.select(CATEGORIES, messages.CAT,
                                      **menu_kwargs).strip()
    if category == '':
        return
    if category not in (CATEGORIES + LANGUAGES):
        # Broadcast.all(f'Invalid type category: {category}.')
        return
    Snippet.purge()
    list_file_path = Path(config.repo, f'{category}.csv')
    if not list_file_path.exists():
        Broadcast.all(messages.CSV_MISSING, 4)
        return
    with open(list_file_path, 'r', encoding='utf-8') as list_contents:
        reader = Snippet.csv_reader(list_contents)
        for i in reader:
            if category in CATEGORIES:
                kwargs = {
                    'description': i[0],
                    'tags': i[1],
                    'category': i[2],
                    'prefix': i[3],
                    'uuid': i[4],
                }
                OpSnippet(**kwargs)
            else:
                kwargs = {
                    'description': i[0],
                    'tags': i[1],
                    'category': i[2],
                    'uuid': i[4],
                }
                CodeSnippet(**kwargs)
    snippets = [str(instance) for instance in Snippet.instances()]
    if len(snippets) == 0:
        Broadcast.all(messages.CAT_EMPTY, 0)
        return
    selected_snippet = config.menu.select(snippets, messages.SNIPPET,
                                          **menu_kwargs)
    if selected_snippet == '':
        return
    description = selected_snippet.partition('|')[0].rstrip()
    snippet = Snippet.get_by_description(description)
    snippet.delete()
    Broadcast.all(f'{messages.SNIPPET_DELETED}\n{snippet.description}')


def del_code_snippet() -> None:
    """Function wrapper of `del_snippet()`, but for code snippets."""
    del_snippet(code=True)


def main(houdini: bool = False) -> None:
    """Get user command.

    Main function of the program. It determines what command user wants to run
    and runs a function bound to that command.

    Args:
        houdini (bool, optional):
            Defines whether the function was run from Houdini or not. Value
            of this parameter determines which function is will be called.

    """
    config = Config()
    other_commands = {
        'opfetch': get_snippet,
        'opdel': del_snippet,
        'codeadd': add_code_snippet,
        'codefetch': get_code_snippet,
        'codedel': del_code_snippet,
    }
    if houdini is True:
        add_op_snippet()
        return
    menu_kwargs = {
        'theme': config.theme,
    }
    cmd = config.menu.select(
        list(other_commands), messages.HOUCLIP, **menu_kwargs).rstrip()
    if cmd == '':
        return
    if cmd not in other_commands:
        Broadcast.all(messages.CMD_INVALID, 2)
        return
    other_commands[cmd]()
