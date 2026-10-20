# This project

`linkedin` CLI (Python, stdlib only) plus two Claude Code skills that write LinkedIn
drafts into the second brain. Drafts Bernardo approves in the review file are published
through the LinkedIn API by `linkedin publicar`
(docs/adr/0003-publish-approved-drafts-through-the-linkedin-api.md).

## Commands

```bash
# Build
uv sync

# Test — the whole suite
uv run pytest

# Test — one file (used after every task; scope, not suite)
uv run pytest tests/<file>.py

# Lint
uv run ruff check . && uv run ruff format --check .

# Format
uv run ruff format .
```

## Conventions

- **Branch names:** `feat/<slug>`, `fix/<slug>`
- **Commits:** Conventional Commits
- **Language:** code and docs in English; CLI subcommands, draft frontmatter and post
  text in Portuguese, because they live in the second brain.
- **Anything a new contributor gets wrong on their first try:** tests never read the real
  second brain, ai-memory or `~/.claude`; every path comes from `config.toml` and tests
  build their own in `tmp_path`.

## Boundaries

- `config.toml`, `dossies/` and `.estado/` hold personal data and are gitignored. Only
  `config.example.toml` is committed.
- The second brain is the user's: the skills only add drafts under its LinkedIn folder;
  `linkedin publicar` only writes the review file and a draft's `status` and `link`.
- The LinkedIn token lives in `~/.config/linkedin-ia/token.json` (0600), never in this
  repository, a draft or a log. Tests never call LinkedIn: the transport is injected.
