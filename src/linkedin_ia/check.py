"""The confidentiality check: what must never reach a public post."""

from dataclasses import dataclass
from pathlib import Path

from linkedin_ia.config import Config


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    text: str


def check(path: Path, config: Config) -> list[Finding]:
    return []
