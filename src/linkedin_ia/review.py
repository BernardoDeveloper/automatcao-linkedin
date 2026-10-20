"""The review file: where Bernardo ticks the drafts that may be published."""

import re

TICK = re.compile(r"^\s*- \[([ xX])\] \[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def ticks(text: str) -> dict[str, bool]:
    """Each checkbox line's draft stem, and whether it is ticked."""
    found = {}
    for line in text.splitlines():
        match = TICK.match(line)
        if match:
            found[match.group(2).strip()] = match.group(1) != " "
    return found
