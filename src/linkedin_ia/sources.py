"""One collector per source; each returns the AI-related items of a window."""

import json
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from linkedin_ia.config import Config

NOTE_EXCLUDED_DIRS = (".obsidian", "_templates", ".git", ".trash")


@dataclass(frozen=True)
class Item:
    source: str
    date: datetime
    origin: str
    text: str


def keyword_pattern(keywords: Iterable[str]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True))
    return re.compile(rf"\b(?:{alternatives})\b", re.IGNORECASE)


URL = re.compile(r"https?://\S+")


def mentions(keywords: re.Pattern[str], text: str) -> int:
    return len(keywords.findall(URL.sub(" ", text)))


def _mtime(path: Path, since: datetime) -> datetime | None:
    modified = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    return modified if modified >= since else None


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def _markdown(
    source: str,
    root: Path,
    since: datetime,
    keywords: re.Pattern[str],
    minimum: int,
    skip: Iterable[Path],
    skip_file: re.Pattern[str] | None = None,
) -> list[Item]:
    skip = [p.resolve() for p in skip]
    items = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part in NOTE_EXCLUDED_DIRS for part in relative.parts):
            continue
        if any(path.resolve().is_relative_to(s) for s in skip):
            continue
        if skip_file and skip_file.fullmatch(path.name):
            continue
        modified = _mtime(path, since)
        if modified is None:
            continue
        body = _strip_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        if mentions(keywords, f"{relative}\n{body}") >= minimum:
            items.append(Item(source, modified, str(relative), body))
    return items


def second_brain(config: Config, since: datetime) -> list[Item]:
    return _markdown(
        "second-brain",
        config.second_brain,
        since,
        keyword_pattern(config.keywords),
        config.min_mentions,
        skip=[config.drafts_dir],
    )


def ai_memory(config: Config, since: datetime) -> list[Item]:
    return _markdown(
        "ai-memory",
        config.ai_memory,
        since,
        keyword_pattern(config.keywords),
        config.min_mentions,
        skip=[],
        skip_file=re.compile(r"log-.*\.md|_meta\.md"),
    )


def _repositories(roots: Iterable[Path]) -> list[Path]:
    return sorted(
        child
        for root in roots
        if root.is_dir()
        for child in root.iterdir()
        if (child / ".git").exists()
    )


def git(config: Config, since: datetime) -> list[Item]:
    items = []
    for repo in _repositories(config.repo_roots):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "log",
                "--all",
                f"--since={since.isoformat()}",
                f"--author={config.author_email}",
                "--format=%cI%x09%s",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            date, _, subject = line.partition("\t")
            items.append(Item("git", datetime.fromisoformat(date), repo.name, subject))
    return items


def _project_name(directory: str) -> str:
    """Claude Code names a session folder after its cwd: `-home-eu-dev-agente` is `agente`."""
    name = re.sub(r"^-home-[^-]+-?", "", directory)
    return name.removeprefix("dev-") or "~"


def claude_sessions(config: Config, since: datetime) -> list[Item]:
    keywords = keyword_pattern(config.keywords)
    items = []
    for path in config.claude_sessions.glob("*/*.jsonl"):
        if _mtime(path, since) is None:
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "user":
                continue
            content = (entry.get("message") or {}).get("content")
            if not isinstance(content, str) or content.lstrip().startswith("<"):
                continue
            stamp = entry.get("timestamp")
            if not stamp:
                continue
            date = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if date < since or mentions(keywords, content) < 1:
                continue
            items.append(Item("claude", date, _project_name(path.parent.name), content))
    return items
