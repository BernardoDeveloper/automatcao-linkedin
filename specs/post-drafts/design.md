# Post drafts — design

## What changes

Serves R1.1–R1.3, R2.1–R2.6, R3.1–R3.3, R4.1–R4.3.

The writing lives in two skills, the queue in the CLI (adr:0002-claude-code-headless-as-the-writer).

- `.claude/skills/linkedin-rascunhos/SKILL.md` — the weekly run. Steps: `uv run linkedin
  coletar`, read the digest, `uv run linkedin fila` to see existing themes, pick up to
  three themes by pillar, write each draft from `references/modelo.md`, run `uv run
  linkedin checar`, add the review task.
- `.claude/skills/linkedin-apresentacao/SKILL.md` — after a talk. Takes a file path, an
  artifact link or pasted notes; asks for date and audience when missing; writes one
  draft and runs the check.
- `.claude/skills/linkedin-rascunhos/references/voz.md` — the voice guide both skills
  read: practitioner sharing what worked and what did not, one concrete thing per post,
  a first line that survives LinkedIn's "ver mais" cut (about 210 characters), short
  paragraphs, at most three hashtags, no emoji bullets, a closing question.
- `.claude/skills/linkedin-rascunhos/references/modelo.md` — the draft template (R1.2),
  shared by both skills.

The drafts folder is `02-Areas/Carreira/LinkedIn/Posts/` in the second brain, from
config. It follows the second brain's own conventions (frontmatter on every note,
`[[wikilinks]]`, tasks in `TAREFAS.md`) and the existing X thread draft
(`02-Areas/Drones/Publicacao X/`), so the queue is readable in Obsidian.

Both skills open by stating that what they read is data, not instructions (R2.6). That is
the soft half; the hard half is the weekly run's tool grant in `scripts/instalar-agenda.sh`
(`--permission-mode dontAsk`, reads and edits scoped to the skills, the digests, the second
brain and the drafts folder, the repository itself never writable), so a digest item that
talks the model into editing `src/` is denied rather than executed by the next
`uv run linkedin`.

`src/linkedin_ia/drafts.py` parses a draft's frontmatter (flat `key: value` and inline
`[a, b]` lists; no YAML dependency) and `linkedin fila` prints the queue, reusing
`check()` from `specs/confidentiality-check/`.

## Data

Status moves `ideia → rascunho → aprovado → publicado`. The skills only ever write
`rascunho`; Bernardo moves it to `aprovado`, posts it, and sets `publicado` with `link`.
Pillars: `aprendizado` (something learned), `bastidor` (how something was built),
`apresentacao` (a talk), `opiniao` (a take on AI news or practice).
