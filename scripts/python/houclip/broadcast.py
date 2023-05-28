#!/bin/python3
"""Handle message broadcasting through various channels.

Four different methods of displaying messages are supported:

1. Standard output --- `Broadcast.stdout()`.
2. Houdini status messages --- `Broadcast.status_msg()`
   (requires `hou` module).
3. Through ``libnotify4`` --- `Broadcast.notify_send()`.
4. All of the above --- `Broadcast.all()`.

All of those methods accept an optional argument ``severity``,
defining the message severity level in accordance to `hou.severityType`:

https://www.sidefx.com/docs/houdini/hom/hou/severityType.html

Some methods may translate these levels into their own severity
structure. For example, because ``libnotify4`` implements "Desktop
Notifications Specification", it only has three ugrency (severity) levels,
so `notify_send()` arbitrarily consolidates them internally.

Severity levels defined by `hou.severityType` are: ``0`` (message),
``1`` (important message), ``2`` (warning), ``3`` (error), ``4`` (fatal).

"""

import subprocess
from abc import ABC


class Broadcast(ABC):
    """Handle message broadcasting through available channels."""

    @staticmethod
    def stdout(msg: str, severity: int = 0) -> None:
        """Print a message to standard output.

        Args:
            msg (str): The message to be printed to standard output.
            severity (int, optional): Message severity.

        """
        severity_names = ('', 'Important!', 'Warning!', 'Error!', 'Fatal!')
        print(f'houclip: {severity_names[severity]} {msg}')

    @staticmethod
    def notify_send(msg: str, severity: int = 0,
                    summary: str = 'Houclip') -> None:
        """Send desktop notification using ``notify-send``.

        Args:
            msg (str): Message to be sent.
            severity (int, optional): Message severity.
            summary (str, optional): Message summary.

        """
        params = {
            0: ['low', 'dialog-information'],
            1: ['low', 'dialog-information'],
            2: ['normal', 'dialog-warning'],
            3: ['critical', 'dialog-error'],
            4: ['critical', 'dialog-error'],
        }
        cmd = (
            f'notify-send -a "houclip" -u {params[severity][0]} '
            f'-i "{params[severity][1]}" "{summary}" "{msg}"'
        )
        subprocess.run(
            cmd,
            check=True,
            shell=True,
            text=True,
            universal_newlines=True,
        )

    @staticmethod
    def status_msg(msg: str, severity: int = 0) -> None:
        """Display status message in Houdini.

        This method requires access to `hou` module.
        It will abort if this requirement is unmet.

        Args:
            msg (str): Status message contents.
            severity (int, optional): Message severity.

        """
        try:
            import hou
        except ModuleNotFoundError:
            return
        severity_types = (
            hou.severityType.Message,
            hou.severityType.ImportantMessage,
            hou.severityType.Warning,
            hou.severityType.Error,
            hou.severityType.Fatal
        )
        hou.ui.setStatusMessage(msg, severity=severity_types[severity])

    @staticmethod
    def all(msg: str, severity: int = 0) -> None:
        """Broadcast a message to all available "channels".

        This method attempts to broadcast message accross all available
        channels.

        Args:
            msg (str): The message to be printed to standard output.
            severity (int, optional): Message severity.

        """
        Broadcast.stdout(msg, severity)
        Broadcast.status_msg(msg, severity)
        Broadcast.notify_send(msg, severity)
