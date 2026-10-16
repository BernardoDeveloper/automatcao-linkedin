---
autonomy: auto
ci: wait
status: approved
checksum: ed5cdd17506a71d9828062d7e3f2b555e33e5c9aa171bc7f31bccd606c4a8621
---

# LinkedIn content on AI

Turn what Bernardo is learning and doing with AI — notes in the second brain, ai-memory
pages, commits, Claude Code sessions, talks given at work — into LinkedIn drafts he
reviews and posts himself, on a weekly rhythm.

## Why

He builds and teaches AI tooling (spec-driven agents, RAG for Protheus, the "IA no Dia a
Dia do Dev" talk at TOTVS) and none of it is visible outside the team. Writing posts from
scratch every week does not happen; reviewing a draft that already cites what he did
does. Done means a weekly run leaves reviewed-ready drafts in the second brain, every
draft passes the confidentiality check before he can approve it, and the first batch is
written from the material that already exists.

## Paths

- `src/linkedin_ia/` — the `linkedin` CLI: `coletar`, `checar`, `fila`
- `.claude/skills/linkedin-rascunhos/`, `.claude/skills/linkedin-apresentacao/`
- `scripts/` — systemd user timer for the weekly run
- `~/Documents/second-brain/02-Areas/Carreira/LinkedIn/` — where drafts live

## References

- `specs/source-digest/` — collect AI-related activity from every source into one digest
- `specs/confidentiality-check/` — block drafts that leak internal TOTVS material
- `specs/post-drafts/` — turn a digest or a talk into drafts in the second brain
- `adr:0001-drafts-only-no-linkedin-api`
- `adr:0002-claude-code-headless-as-the-writer`

## Out of scope

- Publishing to LinkedIn by API or browser automation (see adr:0001).
- Instagram, X and FPV brand content — that is the Marca-Pessoal area.
- Carousel PDFs and generated images; a later plan, once text posts have a rhythm.
- Analytics of post reach.

## Tasks

### 1 · Base

- [x] 1.1 (Unit) Fill project.md, stack.md, glossary and the two ADRs
- [x] 1.2 (Unit) Scaffold the Python package with uv, ruff, pytest and the CLI entry point
  _Depends 1.1_
- [x] 1.3 (Unit) Add the GitHub Actions workflow running ruff and pytest
  _Depends 1.2_

### 2 · Rollout

- [x] 2.1 (Unit) Add the systemd user timer that runs the weekly drafts skill headless
  _Depends 1.2_
- [x] 2.2 (Unit) Register the project and the LinkedIn folder in the second brain
- [x] 2.3 (Unit) Write the first batch of drafts from the material already in the second brain and the dev projects
  _Depends 2.2_
- [x] 2.4 (Unit) Scope the weekly run's tools with dontAsk, add a timeout, refuse unsafe
      paths
  _Reason security review finding_

## Done when

- `uv run linkedin coletar` writes a digest with items from the second brain, git and Claude sessions.
- `uv run linkedin checar` exits 2 on a draft containing a Jira key or a `.prw` file name.
- `uv run linkedin fila` lists at least two drafts in the second brain, each passing `checar`.
- `systemctl --user list-timers` shows `linkedin-rascunhos.timer`.
- `scc validate` exits 0 and CI is green on the PR.
