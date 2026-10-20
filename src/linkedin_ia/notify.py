"""Desktop notifications through notify-send."""

import shutil
import subprocess
from collections.abc import Callable

Notifier = Callable[[str], None]


def desktop(text: str) -> None:
    """Show `text` under the title LinkedIn; do nothing where notify-send is missing."""
    command = shutil.which("notify-send")
    if command is None:
        return
    subprocess.run(
        [command, "--app-name=linkedin", "--", "LinkedIn", text], check=False, timeout=10
    )
