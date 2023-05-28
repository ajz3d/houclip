#!/bin/python3
"""Contains abstract class interacting with X11 clipboard."""
import subprocess
from pathlib import Path
from abc import ABC


class Clipboard(ABC):
    """Abstract class for handling clipboard interaction."""

    @staticmethod
    def get() -> str:
        """Get X11 clipboard contents.

        Returns:
            str: Clipboard contents.

        """
        with subprocess.Popen(
                ['xsel', '-b'],
                stdout=subprocess.PIPE,
                text=True,
        ) as proc:
            return proc.stdout.read()

    @staticmethod
    def fetch(source_file: Path) -> None:
        """Copy text from file to X11 clipboard.

        Args:
            source_file (Path): File to read from.

        """
        cmd = f'xclip -sel clip < "{source_file}"'
        subprocess.run(
            cmd,
            check=True,
            shell=True,
            text=True,
            universal_newlines=True,
        )
