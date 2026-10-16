# Source digest — design

## What changes

Serves R1.1–R1.6, R2.1–R2.4, R3.1–R3.3.

`src/linkedin_ia/config.py` loads `config.toml` (`tomllib`) into a frozen dataclass:
source paths, author email, repository roots, keywords, default window days, item cap,
excerpt length, internal domains and forbidden terms (the last two are read by
`specs/confidentiality-check/`). A missing `config.toml` falls back to
`config.example.toml` so `uv run linkedin` works on a fresh clone.

`src/linkedin_ia/sources.py` has one function per source, each
`(config, since: datetime) -> list[Item]`, `Item` being `(source, date, origin, text)`.
They never raise on a missing path: the caller checks existence first and records the
source as skipped (R1.6).

- Second brain and ai-memory: walk `*.md`, filter by `mtime`, then by keyword over the
  file text. The excerpt is the title line plus the start of the body, frontmatter cut.
- Git: `git log --since=<iso> --author=<email> --format=%cI%x09%s` per repository
  found one level under each root. No keyword filter: a commit subject rarely names the
  technology, and the repository name gives the model the context.
- Claude sessions: each `*.jsonl` under `~/.claude/projects/` whose `mtime` is in the
  window; keep entries with `type == "user"` whose `message.content` is a string not
  starting with `<` (harness messages, command tags, task notifications) and whose
  `timestamp` is in the window.

Keyword match is `\b<keyword>\b`, `re.IGNORECASE`, over the text. `IA` is a keyword, so
the word boundary is what keeps "dia" and "Bahia" out.

`src/linkedin_ia/digest.py` renders the Markdown and `src/linkedin_ia/state.py` reads and
writes `.estado/ultima-coleta` (an ISO timestamp). The state is written only after the
digest file is, so a failed run repeats its window (R2.4).

## Data

```markdown
# Dossiê 2026-10-16

Janela: 2026-10-02T00:00 → 2026-10-16T19:20

## Second brain (3)

- 2026-10-05 · `06-Documentos/Carreira/Guia IA no dia a dia - AdvPL TLPP.md`
  > Guia IA no dia a dia — AdvPL e TLPP. Guia de 3 páginas que acompanha …

## Pulado

- ai-memory: `/caminho/inexistente` não existe
```
