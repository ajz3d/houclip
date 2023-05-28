"""Contains classes for user interaction via Dmenu clones."""
import subprocess
from abc import ABC, abstractmethod


class Menu(ABC):
    """Base abstract class for classes that handle user interaction."""

    @staticmethod
    @abstractmethod
    def enter(prompt: str, **kwargs) -> str:
        """Show menu and let user input a string.

        Args:
            prompt (str):
                Text to display as prompt.
            **kwargs: Arbitrary list of arguments.

        Returns:
            str: User input.
        """

    @staticmethod
    @abstractmethod
    def select(input_: list[str], prompt: str = None, **kwargs):
        r"""Given an item list, let user select one from the menu.

        Args:
            input\_ (list[str]): A list of menu items to display.
            prompt (str, optional): Text to display as prompt.
            **kwargs: Arbitrary list of arguments.

        Returns:
            str: User selection.

        """


class Dmenu(Menu):
    """Handle interaction via ``dmenu``."""

    @staticmethod
    def enter(prompt: str, **kwargs) -> str:
        """Show rofi menu and let user input a string.

        Args:
            prompt (str): Text to display as prompt.
            **kwargs:
                If ``kwargs['theme']`` key exists, its value will be used
                to generate a theme-setting rofi option.

        Returns:
            str: User input.

        """
        command = f'dmenu -p "{prompt}" < /dev/null'
        with subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE,
                universal_newlines=True
        ) as proc:
            stdout = proc.stdout.readline().rstrip()
        return stdout

    @staticmethod
    def select(input_: list[str], prompt: str = None, **kwargs) -> str:
        r"""Given an item list, let user select one of them.

        Args:
            input\_ (list[str]): A list of menu items to display.
            prompt (str, optional): Text to display as prompt.
            **kwargs:
                If ``kwargs['theme']`` key exists, its value will be used
                to generate a theme-setting rofi option.

        Returns:
            str: User selection.

        """
        input_ = '\n'.join(list(input_))
        command = "dmenu -i -l 25"
        with subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE,
                stdin=subprocess.PIPE, universal_newlines=True
        ) as proc:
            stdout, _ = proc.communicate(input=input_)
        return stdout


class Rofi(Menu):
    """Handle interaction via ``rofi``."""

    @staticmethod
    def enter(prompt: str, **kwargs) -> str:
        command = (f'rofi {Rofi.__theme_option(kwargs["theme"])}'
                   f'-dmenu -p "{prompt}"')
        with subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE,
                universal_newlines=True, text=True
        ) as proc:
            stdout, _ = proc.communicate()
        return stdout.rstrip()

    @staticmethod
    def select(input_: list[str], prompt: str = None, **kwargs) -> str:
        input_ = '\n'.join(list(input_))
        command = (f'rofi {Rofi.__theme_option(kwargs["theme"])}'
                   f'-dmenu -i -p "{prompt or ""}"')
        with subprocess.Popen(
                command, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, universal_newlines=True,
                text=True
        ) as proc:
            stdout, _ = proc.communicate(input=input_)
        return stdout

    @staticmethod
    def __theme_option(theme: str) -> str:
        """Return Rofi command for setting theme or empty string.

        Args:
            theme (str): Selected Rofi theme.

        Returns:
            str:
                Rofi option for setting the selected theme,
                or an empty string.

        """
        if theme == '' or theme is None:
            return ''
        return f'-theme {theme} '


MENUS = {
    'Dmenu': Dmenu,
    'Rofi': Rofi,
}
"""dict: Dictionary of available menu classes."""
