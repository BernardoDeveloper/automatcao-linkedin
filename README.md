# automatcao-linkedin

Turns what I learn and build with AI into LinkedIn drafts in my second brain. I review
and post them myself — nothing here publishes (docs/adr/0001-drafts-only-no-linkedin-api.md).

```
second brain · ai-memory · git · Claude Code sessions
        └── linkedin coletar ──> dossies/AAAA-MM-DD.md
                └── /linkedin-rascunhos (claude -p) ──> second-brain/02-Areas/Carreira/LinkedIn/Posts/
                        └── linkedin checar ──> I review, post, set status: publicado
```

## Setup

```bash
uv sync
cp config.example.toml config.toml   # set email_autor, termos_proibidos, dominios_internos
scripts/instalar-agenda.sh           # weekly run, Mondays 08:30 (--remover to undo)
```

## Use

| | |
|---|---|
| `uv run linkedin coletar [--desde AAAA-MM-DD]` | write the digest of AI activity since the last run |
| `uv run linkedin checar <draft>...` | confidentiality check; exit 2 on findings |
| `uv run linkedin fila` | drafts by status; exit 2 if an approved draft fails the check |
| `/linkedin-rascunhos` in Claude Code | 1–3 drafts from the digest |
| `/linkedin-apresentacao` in Claude Code | one draft about a talk given at work |
| `systemctl --user start linkedin-rascunhos` | run the weekly job now |

Plan: `plans/linkedin-conteudo-ia.md` · specs: `specs/source-digest/`,
`specs/confidentiality-check/`, `specs/post-drafts/` · voice guide:
`.claude/skills/linkedin-rascunhos/references/voz.md`.
