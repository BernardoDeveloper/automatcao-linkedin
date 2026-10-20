# Stack

Every adopted technology, with one line on why it earned its place. Technology not
listed here is an open decision.

## Runtime

- **Python 3.12** — the deterministic half (digest, confidentiality check, queue); stdlib
  only, `tomllib` for config, so the CLI has no runtime dependencies to keep current.
- **Claude Code (`claude -p`)** — writes the drafts from the digest, see
  adr:0002-claude-code-headless-as-the-writer.
- **LinkedIn REST API** (Posts, Images, Comments, `userinfo`; product "Share on LinkedIn") — the
  only sanctioned way to post as a member, see adr:0003-publish-approved-drafts-through-the-linkedin-api;
  called with `urllib`, so no HTTP dependency.
- **notify-send** (libnotify) — desktop notifications; already on the Ubuntu desktop.
- **systemd user timer** — the weekly run; already on the machine, survives reboots and
  catches up a missed run with `Persistent=true`.

## Development

- **uv** — environment, lockfile and `uv run`; already what the machine uses for Python.
- **pytest** — the test suite CI runs.
- **ruff** — lint and format in one tool.
- **GitHub Actions** — CI on every PR.
