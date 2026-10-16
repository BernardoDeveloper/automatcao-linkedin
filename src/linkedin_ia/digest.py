"""Collects every source into one Markdown digest."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from linkedin_ia import sources
from linkedin_ia.config import Config
from linkedin_ia.sources import Item

TITLES = {
    "second-brain": "Second brain",
    "ai-memory": "ai-memory",
    "git": "Commits",
    "claude": "Sessões do Claude Code",
}


@dataclass
class Collection:
    since: datetime
    until: datetime
    items: dict[str, list[Item]] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)


def _sources(config: Config) -> list[tuple[str, list[Path], Callable[..., list[Item]]]]:
    return [
        ("second-brain", [config.second_brain], sources.second_brain),
        ("ai-memory", [config.ai_memory], sources.ai_memory),
        ("git", list(config.repo_roots), sources.git),
        ("claude", [config.claude_sessions], sources.claude_sessions),
    ]


def collect(config: Config, since: datetime, until: datetime) -> Collection:
    result = Collection(since, until)
    for name, paths, collector in _sources(config):
        missing = [p for p in paths if not p.exists()]
        result.skipped += [f"{name}: `{p}` não existe" for p in missing]
        if len(missing) == len(paths):
            continue
        items = sorted(collector(config, since), key=lambda i: i.date, reverse=True)
        result.items[name] = items[: config.max_items]
    return result


def _excerpt(text: str, length: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= length else flat[: length - 1].rstrip() + "…"


def render(collection: Collection, config: Config) -> str:
    fmt = "%Y-%m-%dT%H:%M"
    lines = [
        f"# Dossiê {collection.until:%Y-%m-%d}",
        "",
        f"Janela: {collection.since:{fmt}} → {collection.until:{fmt}}",
    ]
    for name, items in collection.items.items():
        lines += ["", f"## {TITLES[name]} ({len(items)})", ""]
        for item in items:
            lines.append(f"- {item.date:%Y-%m-%d} · `{_excerpt(item.origin, 200)}`")
            lines.append(f"  > {_excerpt(item.text, config.excerpt_length)}")
    if collection.skipped:
        lines += ["", "## Pulado", ""]
        lines += [f"- {s}" for s in collection.skipped]
    return "\n".join(lines) + "\n"


def write(collection: Collection, config: Config) -> Path:
    config.digest_dir.mkdir(parents=True, exist_ok=True)
    path = config.digest_dir / f"{collection.until:%Y-%m-%d-%H%M%S}.md"
    path.write_text(render(collection, config), encoding="utf-8")
    return path
