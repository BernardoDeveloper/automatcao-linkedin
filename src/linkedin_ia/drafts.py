"""Drafts in the second brain: their frontmatter and the queue."""

from dataclasses import dataclass
from pathlib import Path

from linkedin_ia import check
from linkedin_ia.config import Config

STATUSES = ("ideia", "rascunho", "aprovado", "publicado")
OTHER = "outro"


@dataclass(frozen=True)
class Draft:
    path: Path
    meta: dict[str, str | list[str]]

    @property
    def status(self) -> str:
        return str(self.meta.get("status", ""))

    @property
    def group(self) -> str:
        status = self.status.strip().lower()
        return status if status in STATUSES else OTHER

    @property
    def title(self) -> str:
        return self.path.stem.split(" - ", 1)[-1]


def frontmatter(text: str) -> dict[str, str | list[str]]:
    """Flat `key: value` lines and inline `[a, b]` lists, which is all a draft uses."""
    block = frontmatter_block(text)
    if block is None:
        return {}
    meta: dict[str, str | list[str]] = {}
    for line in block.splitlines():
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


def _split(text: str) -> tuple[list[str], list[str]] | None:
    """Frontmatter lines and body lines, or None when the text has no frontmatter."""
    lines = text.replace("\r\n", "\n").split("\n")
    if lines[0] != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return lines[1:index], lines[index + 1 :]
    return None


def frontmatter_block(text: str) -> str | None:
    parts = _split(text)
    return None if parts is None else "\n".join(parts[0])


def strip_frontmatter(text: str) -> str:
    parts = _split(text)
    return text if parts is None else "\n".join(parts[1]).lstrip("\n")


def post_body(text: str) -> str:
    """The first `## Post` section, without the blank lines around it."""
    sections = check.post_bodies(text)
    return "\n".join(sections[0][1]).strip("\n") if sections else ""


def update(path: Path, fields: dict[str, str]) -> None:
    """Set frontmatter keys in place; keys not yet there go at the end of the block."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    parts = _split(text)
    if parts is None:
        raise ValueError(f"{path}: sem frontmatter")
    head, body = parts
    pending = dict(fields)
    for index, line in enumerate(head):
        key, sep, _ = line.partition(":")
        if sep and not line.startswith((" ", "-")) and key.strip() in pending:
            value = pending.pop(key.strip())
            head[index] = f"{key.strip()}: {value}".rstrip()
    head.extend(f"{key}: {value}".rstrip() for key, value in pending.items())
    path.write_text("\n".join(["---", *head, "---", *body]), encoding="utf-8")


def load(path: Path) -> Draft:
    return Draft(path, frontmatter(path.read_text(encoding="utf-8")))


def queue(config: Config) -> list[Draft]:
    if not config.drafts_dir.is_dir():
        return []
    found = []
    for path in sorted(config.drafts_dir.glob("*.md")):
        try:
            found.append(load(path))
        except (UnicodeDecodeError, OSError):
            continue
    return found
