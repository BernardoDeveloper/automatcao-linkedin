# automatcao-linkedin

Turns what I learn and build with AI into LinkedIn drafts in my second brain. I tick the
ones that may go out in one review file; they are published on their `publicar_em`
through the LinkedIn API (docs/adr/0003-publish-approved-drafts-through-the-linkedin-api.md).

```
second brain · ai-memory · git · Claude Code sessions
        └── linkedin coletar ──> dossies/AAAA-MM-DD-HHMMSS.md
                └── /linkedin-rascunhos (claude -p) ──> second-brain/…/LinkedIn/Posts/
                        └── linkedin publicar ──> …/LinkedIn/Revisão de posts.md + notification
                                I tick [x] ──> next hourly run on publicar_em ──> LinkedIn
```

## Setup

```bash
uv sync
cp config.example.toml config.toml   # set email_autor, termos_proibidos, dominios_internos
scripts/instalar-agenda.sh           # weekly drafts (Mon 08:30) + hourly publish 09-18h
uv run linkedin login                # paste a token, see below; again every 60 days
```

### LinkedIn token

1. At <https://www.linkedin.com/developers/apps> create an app (it asks for a LinkedIn page;
   any page you admin works) and, under **Products**, add **Share on LinkedIn** and
   **Sign In with LinkedIn using OpenID Connect**.
2. Open the [token generator](https://www.linkedin.com/developers/tools/oauth/token-generator),
   pick the app, tick `openid`, `profile` and `w_member_social`, generate.
3. `uv run linkedin login` and paste it. It is stored in `~/.config/linkedin-ia/token.json`
   (mode 0600). A notification warns a week before the 60 days run out.

## Review and publish

- Each run rewrites `Revisão de posts.md` next to the `Posts/` folder. Tick `[x]` to
  approve; untick to withdraw. Editing an approved post sends it back for review.
- Images go in `LinkedIn/Imagens/` with the name the line shows (`.png`, `.jpg` or `.gif`).
- A post with `mencoes` is listed under manual publishing: the API cannot tag people.
- A run publishes approved posts whose `publicar_em` is today or earlier (empty = now),
  fills `link`, sets `status: publicado` and adds `primeiro_comentario` as a comment.

## Use

| | |
|---|---|
| `uv run linkedin coletar [--desde AAAA-MM-DD]` | write the digest of AI activity since the last run |
| `uv run linkedin checar <draft>...` | confidentiality check; exit 2 on findings |
| `uv run linkedin fila` | drafts by status; exit 2 if an approved draft fails the check |
| `uv run linkedin publicar [--simular]` | apply ticks, publish what is due, rewrite the review file |
| `uv run linkedin login` | store the LinkedIn token |
| `/linkedin-rascunhos` in Claude Code | 1–3 drafts from the digest |
| `/linkedin-apresentacao` in Claude Code | one draft about a talk given at work |
| `systemctl --user start linkedin-rascunhos` | run the weekly job now |
| `systemctl --user start linkedin-publicar` | run the publisher now |

Plan: `plans/linkedin-conteudo-ia.md` · specs: `specs/source-digest/`,
`specs/confidentiality-check/`, `specs/post-drafts/`, `specs/automatic-publishing/` · voice guide:
`.claude/skills/linkedin-rascunhos/references/voz.md`.
