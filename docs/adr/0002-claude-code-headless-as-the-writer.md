---
status: accepted
---

# 0002 · Claude Code, run headless, writes the drafts

## Context

Writing a draft means judging which activity is worth a post and phrasing it in
Bernardo's voice — work for a model. The options were calling the Anthropic API from the
CLI, or running Claude Code itself (`claude -p`) with a skill. The sources are local
files (second brain, ai-memory, `~/dev`, `~/.claude/projects`), so a cloud routine
cannot reach them.

## Decision

Deterministic work is Python: collecting sources into a digest, the confidentiality
check, listing the queue. Writing is a Claude Code skill (`/linkedin-rascunhos`), run
weekly by a systemd user timer as `claude -p` from this repository, with its tools
restricted to the `linkedin` CLI and to reading and writing Markdown.

## Consequences

- No API key to store; runs on the existing Claude subscription and its limits.
- The voice guide and the post rules are Markdown in the skill, editable without code.
- The weekly run needs the laptop on; a missed run catches up through `Persistent=true`
  and the digest's "since last run" window.
- Output is not deterministic, so tests cover the CLI, not the prose; the
  confidentiality check is what makes model output safe to approve.
