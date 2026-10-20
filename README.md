# automatcao-linkedin

Turns what you learn and build with AI into LinkedIn posts, with a human approval in
the middle.

Every week a headless Claude Code session reads your recent activity (an Obsidian
vault, commits, Claude Code sessions, ai-memory pages) and writes
one to three drafts in your vault. You get a desktop notification, read the drafts,
tick the ones that may go out in a single Markdown file, and they are published to your
profile on their planned day through LinkedIn's official API.

Nothing is published without a tick, and a tick only covers the exact version you saw.

> The CLI subcommands, the draft frontmatter and the posts are in Brazilian Portuguese,
> because the drafts live in a Portuguese vault. The code and these docs are in English.

## How it works

```
 Obsidian vault · git repos · Claude Code sessions · ai-memory
        │
        │  Mondays 08:30 (systemd timer)
        ▼
 linkedin coletar ─────────────> dossies/AAAA-MM-DD-HHMMSS.md      digest of AI activity
        │
        ▼
 claude -p /linkedin-rascunhos ─> vault/…/LinkedIn/Posts/*.md       1–3 drafts, status: rascunho
        │                          (restricted tools, see Security)
        ▼
 linkedin publicar ────────────> vault/…/LinkedIn/Revisão de posts.md + desktop notification
        │
        │  you: read, add images, tick [x]
        ▼
 linkedin publicar (hourly 09–18h) ─> LinkedIn API ─> status: publicado, link filled
```

| Piece | What it does |
|---|---|
| `linkedin coletar` | Collects AI-related items since the last run into a digest: vault notes, commits authored by you under `~/dev`, Claude Code prompts, ai-memory pages. Deterministic Python, no model. |
| `/linkedin-rascunhos` | A Claude Code skill. Reads the digest, picks up to three themes, writes drafts following a voice guide, runs the confidentiality check until it passes. |
| `/linkedin-apresentacao` | Same, for one post about a talk you gave, from slides or notes. |
| `linkedin checar` | Confidentiality check: issue keys, source file names, internal domains, forbidden terms, e-mails, IPs, credentials, length. |
| `linkedin publicar` | Reads your ticks, records approvals, publishes what is due, rewrites the review file, notifies. |
| `linkedin login` | Stores your LinkedIn access token. |
| `scripts/instalar-agenda.sh` | Installs the two systemd user timers. |

## Requirements

- Linux with a systemd user session and `notify-send` (libnotify). Tested on Ubuntu.
- Python 3.12+ and [uv](https://docs.astral.sh/uv/).
- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and logged in
  (`claude` on your `PATH`): it writes the drafts.
- A folder of Markdown notes for the drafts (an Obsidian vault works best: drafts use
  frontmatter and `[[wikilinks]]`).
- A LinkedIn account and a LinkedIn developer app (free, see below).

## Install

```bash
git clone https://github.com/BernardoDeveloper/automatcao-linkedin.git
cd automatcao-linkedin
uv sync
cp config.example.toml config.toml
```

The scheduled job runs from this folder, so keep the clone where it is (the installer
refuses paths with spaces).

### Configure `config.toml`

`config.toml` is gitignored; only `config.example.toml` is committed. Paths accept `~`.

| Section · key | What it is |
|---|---|
| `fontes.second_brain` | Your vault. |
| `fontes.ai_memory` | ai-memory wiki folder; a missing folder is skipped. |
| `fontes.claude_sessoes` | `~/.claude/projects`, where Claude Code keeps sessions. |
| `fontes.repositorios` | Folders whose direct child git repos are read. |
| `fontes.email_autor` | Your git e-mail: only your commits are collected. |
| `coleta.*` | Window (`dias_padrao`), limits, and the AI keywords an item must mention. |
| `rascunhos.pasta` | Drafts folder, relative to the vault. |
| `rascunhos.revisao` | The review file, relative to the vault. Must be outside the drafts folder. |
| `rascunhos.imagens` | Images folder, relative to the vault. Must be outside the drafts folder. |
| `linkedin.versao` | `LinkedIn-Version` header, `YYYYMM`. LinkedIn retires a version about a year after release; bump it then. |
| `linkedin.token` | Where `linkedin login` stores the token. Keep it outside the repo. |
| `confidencialidade.dominios_internos` | Hosts that must never appear in a post (your company's internal domains). |
| `confidencialidade.termos_proibidos` | Customer names, internal system names: matched as whole words, ignoring case and accents. |
| `confidencialidade.permitidos` | Strings that look like issue keys but are not (`GPT-5`, `ISO-8601`). |

**Fill in `dominios_internos` and `termos_proibidos`.** They are empty by default, and
posts go out on their own once approved; `linkedin checar` warns while they are empty.

### Adapt the voice

The drafts follow `.claude/skills/linkedin-rascunhos/references/voz.md`, written for the
author (a Protheus/AdvPL developer posting about AI in Portuguese). Rewrite it for your
own audience, tone and topics before the first run. The draft template is
`references/modelo.md` next to it.

### Create the LinkedIn app and get a token

1. Go to <https://www.linkedin.com/developers/apps> and create an app. It asks for a
   LinkedIn **company page** you administer. The page only owns the app: nothing is
   posted there, posts go to your personal profile. Any page you admin works; creating
   one takes two minutes. If the app asks for verification, approve the link as the
   page admin.
2. Under **Products**, add **Share on LinkedIn** and **Sign In with LinkedIn using
   OpenID Connect**.
3. Open the [token generator](https://www.linkedin.com/developers/tools/oauth/token-generator),
   pick the app, tick `openid`, `profile` and `w_member_social`, and generate.
4. Store it:

   ```bash
   uv run linkedin login
   ```

   Paste the token when asked (it is not echoed). It is checked against LinkedIn and
   saved to `~/.config/linkedin-ia/token.json` with mode `0600`.

Tokens last **60 days** and self-serve apps get no refresh token, so repeat steps 3–4
every two months; a notification warns a week ahead.

<details>
<summary>"We can't verify the authenticity of your request because the state parameter was modified"</summary>

The generator lost its session cookie mid-flow. Disable browser extensions (ad and
privacy blockers) or use a private window, keep one tab, and approve right away.

If it still fails, do the OAuth flow by hand:

1. In the app's **Auth** tab, add `https://localhost:8765/callback` as a redirect URL and
   note the Client ID and Client Secret.
2. Open, with your Client ID:
   `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=CLIENT_ID&redirect_uri=https%3A%2F%2Flocalhost%3A8765%2Fcallback&state=anything123&scope=openid%20profile%20w_member_social`
3. Allow. The page fails to load, which is expected: copy `code` from the address bar
   (valid for 30 minutes).
4. Exchange it (a leading space keeps the secret out of fish/bash history when
   configured to):

   ```bash
    curl -s -X POST https://www.linkedin.com/oauth/v2/accessToken -d grant_type=authorization_code -d code=CODE -d client_id=CLIENT_ID -d client_secret=CLIENT_SECRET -d redirect_uri=https://localhost:8765/callback
   ```

5. Run `uv run linkedin login` and paste the `access_token`.

</details>

### Turn on the schedule

```bash
scripts/instalar-agenda.sh
```

It installs two systemd user timers:

| Timer | When | Runs |
|---|---|---|
| `linkedin-rascunhos` | Mondays 08:30 | `claude -p /linkedin-rascunhos`, then `linkedin publicar` |
| `linkedin-publicar` | every hour, 09:00–18:00 | `linkedin publicar` |

Both catch up a run missed while the machine was off. Remove them with
`scripts/instalar-agenda.sh --remover`.

Check it works:

```bash
systemctl --user list-timers 'linkedin-*'
systemctl --user start linkedin-publicar
journalctl --user -u linkedin-publicar -n 20
```

After the manual run the review file exists in your vault, and a notification lists
any drafts waiting for review.

## Using it

### Weekly

1. **Monday morning** a notification says *N post(s) para revisar*.
2. Open `Revisão de posts.md` in your vault. Each draft is one line:

   ```
   - [ ] [[2026-10-16 - Spec antes do agente]] · v:e258f97a… · publicar em 2026-10-20 · “Todo mês a galera…” · **falta a imagem** `…/Imagens/2026-10-16 - Spec antes do agente.png`
   ```

3. Open the draft through the `[[link]]`, read it, edit what you want: the post body,
   `publicar_em`, `primeiro_comentario`.
4. If the line says **falta a imagem**, save the image in the images folder under the
   name shown (`.png`, `.jpg` or `.gif`; another extension of the same name is
   accepted). A text-only post: empty the `imagem:` field in the draft.
5. Tick `[x]`.

Order matters: **edit and add the image first, tick last.** The tick covers the version
printed on the line; if the draft, its date or its image changes, before or after the
tick, the draft goes back to review with a notification and you tick it again.

The next hourly run moves ticked drafts to **Aprovados**. On their `publicar_em` (or the
next run, if empty) they are posted, the first comment is added, the draft gets
`status: publicado` and `link:`, and a notification says *Publicado: …*.

To withdraw an approved post, untick it.

### Posts that tag people

LinkedIn's API cannot look up another member, so a draft with `mencoes: [Name]` is
listed under **Publicar manualmente**. Post it yourself, tag the people, then set
`status: publicado` and `link:` in the draft.

### Notifications

| Notification | Meaning | What to do |
|---|---|---|
| *N post(s) para revisar* | New drafts in the review file | Review and tick |
| *Publicado: …* | Posted | Answer comments in the first hour |
| *… saiu sem o primeiro comentário* | The post is up, the comment was refused | Comment by hand |
| *… não saiu: motivo* | Blocked: confidentiality finding, missing image, too long, control characters | Fix the draft, tick again |
| *… não saiu, tento de novo* | LinkedIn refused (4xx) | Retried every hour; check the message |
| *Confira no LinkedIn se … saiu* | No answer, or a server error, while posting | Posted: set `status: publicado`. Not posted: untick and tick again |
| *… mudou e voltou para revisão* | The draft changed after you ticked it | Re-read, tick again |
| *O token do LinkedIn vence em …* / *Sem token* | Token expiring or gone | `uv run linkedin login` |

### Commands

| Command | |
|---|---|
| `uv run linkedin coletar [--desde AAAA-MM-DD]` | Write the digest since the last run |
| `uv run linkedin checar <draft>...` | Confidentiality check; exit 2 on findings |
| `uv run linkedin fila` | Drafts by status |
| `uv run linkedin publicar [--simular]` | Run the publisher; `--simular` prints and changes nothing |
| `uv run linkedin login [--dias 60]` | Store the token |
| `/linkedin-rascunhos` in Claude Code | Write drafts now, interactively |
| `/linkedin-apresentacao` in Claude Code | One draft about a talk you gave |
| `systemctl --user start linkedin-rascunhos` | Run the weekly job now |
| `systemctl --user start linkedin-publicar` | Run the publisher now |

## Draft format

One Markdown file per post in the drafts folder, named `AAAA-MM-DD - Título.md`:

```markdown
---
tipo: publicacao
publicar_em: 2026-10-22          # day it goes out; empty = next run after approval
pilar: bastidor                  # aprendizado · bastidor · apresentacao · opiniao
status: rascunho                 # ideia → rascunho → aprovado → publicado
link:                            # filled when published
imagem: 2026-10-16 - Título.png  # file in the images folder; empty = text only
primeiro_comentario: Link: https://…   # posted as the first comment
mencoes: []                      # names to tag; non-empty = manual publishing
fontes: ["[[Note]]", "git: repo"]
tags: [linkedin, ia]
---
# Título

## Resumo
…

## Post

The exact text that goes to LinkedIn. Hashtags like #IA stay hashtags.

## Checklist antes de aprovar
…
```

Only the `## Post` section is published. The 3000-character LinkedIn limit applies to
it, 1250 to the first comment.

## Security model

The weekly agent reads text you did not write (commit messages, notes, session logs),
so it is treated as potentially prompt-injected. The design keeps it from publishing
anything on its own:

- **Restricted tools.** It runs with `--permission-mode dontAsk` and may only read the
  vault and the digests, write in the drafts folder, and run `linkedin coletar`, `fila`
  and `checar`. It cannot edit this repository, the review file, the images folder or
  the approval state, and cannot run `publicar` or `login`.
- **Approval outside its reach.** An approval is a tick in the review file, recorded in
  `.estado/publicacao.json` with a SHA-256 fingerprint of the post body, first comment,
  date and image. `status: aprovado` written into a draft approves nothing.
- **A tick covers what you saw.** Each line carries a 128-bit version of the draft; a
  tick on an older version approves nothing, and any change after approval voids it.
  Values written into the review file are escaped so a crafted draft cannot forge a
  ticked line.
- **Checked right before posting.** The confidentiality check runs again on the body and
  the first comment, from the same read that is sent.
- **Never twice.** A marker is saved before each post request. A 4xx is retried; a 5xx,
  a redirect or a missing answer is never retried, you are asked to check by hand. A
  version already published is never approved again.
- **Token.** Stored `0600` outside the repo, never printed or logged, sent only to
  `api.linkedin.com` and LinkedIn upload hosts; redirects are not followed.

Decisions and their reasons: `docs/adr/`. Full requirements: `specs/`.

## Limitations

- Posting needs the machine on: a post goes out at the first run on or after its date.
- No mentions, video, documents, carousels or several images.
- The review line shows the start of the post; open the draft to read all of it.
- LinkedIn may refuse comments with a "Share on LinkedIn" token; the post still goes out.

## Development

```bash
uv sync
uv run pytest                                   # whole suite; never touches the network
uv run ruff check . && uv run ruff format --check .
```

Tests never read your vault, ai-memory or `~/.claude`: every path comes from config and
tests build their own under `tmp_path`; the HTTP transport is injected.

The repository is spec-driven with [scc](https://www.npmjs.com/package/@protonspy/scc):

| Path | |
|---|---|
| `src/linkedin_ia/` | The CLI (stdlib only) |
| `.claude/skills/linkedin-*` | The drafts skills and the voice guide |
| `specs/` | Requirements, design and tasks per feature |
| `docs/adr/` | Decisions that are hard to reverse |
| `docs/glossary.md`, `docs/stack.md` | Terms and adopted technology |
| `scripts/instalar-agenda.sh` | systemd timers |
