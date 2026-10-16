"""Drafts in the second brain: their frontmatter and the queue."""

from dataclasses import dataclass
from pathlib import Path

from linkedin_ia.config import Config

STATUSES = ("ideia", "rascunho", "aprovado", "publicado")
CHECKED = ("rascunho", "aprovado")


@dataclass(frozen=True)
class Draft:
    path: Path
    meta: dict[str, str | list[str]]

    @property
    def status(self) -> str:
        return str(self.meta.get("status", ""))

    @property
    def title(self) -> str:
        return self.path.stem.split(" - ", 1)[-1]


def frontmatter(text: str) -> dict[str, str | list[str]]:
    """Flat `key: value` lines and inline `[a, b]` lists, which is all a draft uses."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    meta: dict[str, str | list[str]] = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if not sep or line.startswith((" ", "-")):
            continue
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [
                v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()
            ]
        else:
            meta[key.strip()] = value.strip("\"'")
    return meta


def load(path: Path) -> Draft:
    return Draft(path, frontmatter(path.read_text(encoding="utf-8")))


def queue(config: Config) -> list[Draft]:
    if not config.drafts_dir.is_dir():
        return []
    return [load(p) for p in sorted(config.drafts_dir.glob("*.md"))]
