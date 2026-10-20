# Automatic publishing — design

## What changes

Serves R1.1–R1.8, R2.1–R2.9, R3.1–R3.4, R4.1–R4.2.

Governed by adr:0003-publish-approved-drafts-through-the-linkedin-api, which supersedes
adr:0001-drafts-only-no-linkedin-api.

Two subcommands join `coletar`, `checar` and `fila`:

- `linkedin login` — reads the token with `getpass`, calls `GET /v2/userinfo` for the
  member's `sub`, and writes `{access_token, person_urn, name, expires_at}` to the token
  file with mode `0600`. The token comes from the Developer Portal's token generator,
  which issues 60-day tokens; `expires_at` is now + 60 days.
- `linkedin publicar [--simular]` — the publish run, in this order: take the lock, read
  ticks from the review file, apply approvals (R1.3, R1.4), drop stale ones (R1.5),
  publish what is due (R2), rewrite the review file (R1.1), send notifications.

New modules under `src/linkedin_ia/`:

- `little.py` — `commentary(body)`: escapes `| { } @ [ ] ( ) < > # \ * _ ~` with a
  backslash and turns each `#Word` at a word start into `{hashtag|\#|Word}` (R2.6).
- `review.py` — reads ticks (`- [x] [[<draft stem>]]` / `- [ ] [[<draft stem>]]`) and
  renders the review file. A draft is keyed by its file stem.
- `linkedin_api.py` — the HTTP client over `urllib`, with the transport injected so
  tests never reach the network. Every call sends `Authorization: Bearer`,
  `LinkedIn-Version` and `X-Restli-Protocol-Version: 2.0.0`.
- `publishing.py` — the publish run and its state.
- `notify.py` — `notify-send "LinkedIn" <text>`; silent when the command is missing.

`drafts.py` gains `post_body()` (the `## Post` section, trimmed) and `update()`, which
rewrites given frontmatter keys in place and leaves every other line untouched.

### API calls

| Step | Request |
|---|---|
| member | `GET https://api.linkedin.com/v2/userinfo` (scopes `openid profile`) |
| image | `POST /rest/images?action=initializeUpload` with `owner` = person URN, then `PUT` the bytes to `uploadUrl` |
| post | `POST /rest/posts`: `author`, `commentary`, `visibility: PUBLIC`, `distribution.feedDistribution: MAIN_FEED`, `lifecycleState: PUBLISHED`, `content.media.id` when there is an image; the post URN comes back in `x-restli-id` |
| comment | `POST /rest/socialActions/{post urn}/comments` with `actor`, `object`, `message.text` |

The link is `https://www.linkedin.com/feed/update/<post urn>/`. The comment endpoint
lists `w_member_social_feed` while the Posts API says `w_member_social` covers comments;
which one a token generated for "Share on LinkedIn" carries is unverified, hence R2.4.

### Schedule

`scripts/instalar-agenda.sh` also installs `linkedin-publicar.timer`
(`OnCalendar=*-*-* 09..18:00:00`, `Persistent=true`), and the weekly drafts service runs
`uv run linkedin publicar` as `ExecStartPost`, replacing its fixed notification. The
headless drafts agent is not granted `linkedin publicar`, `linkedin login`, the review
file or the state.

## Data

Config, all optional with these defaults:

```toml
[rascunhos]
revisao = "02-Areas/Carreira/LinkedIn/Revisão de posts.md"   # relative to second_brain
imagens = "02-Areas/Carreira/LinkedIn/Posts/imagens"

[linkedin]
versao = "202610"                                # LinkedIn-Version header, YYYYMM
token = "~/.config/linkedin-ia/token.json"
```

Draft frontmatter, all optional (delta to specs/post-drafts/R1.2): `imagem` (file name
in the images folder; another extension of the same stem is accepted),
`primeiro_comentario`, `mencoes` (inline list of names).

State in `.estado/publicacao.json`:

```json
{
  "aprovacoes": {"<stem>": "<sha256>"},
  "publicando": {"<stem>": "<iso time the request started>"},
  "avisados": ["<stem>:<reason>:<date or ''>"]
}
```

The fingerprint is SHA-256 over the post body, the first comment and the image bytes.
`publicando` is written before the post request and removed once the draft is updated;
an entry left behind means the request never answered (R2.8). `avisados` holds one key
per notification already sent: draft keys (R1.8, R2.5) carry no date, the token keys
(R3.3, R3.4) carry today's date so they repeat daily.

## Alternatives considered

- **Approval by frontmatter status.** Rejected: the weekly agent reads untrusted text and
  can write drafts, so it could write `status: aprovado` itself. The review file sits
  outside its write grant and the approval lives in `.estado/`, bound to a fingerprint,
  so an edit after approval — by anyone — sends the draft back to review.
- **Local OAuth flow** (`client_id`/`client_secret` plus a callback server on
  `localhost`). Rejected for now: LinkedIn issues no refresh token to self-serve apps, so
  it still means a browser login every 60 days, and it adds a stored secret and a
  listening socket. Pasting from the token generator costs the same two minutes.
- **Notification per hourly run.** Rejected: one notification per draft and reason, kept
  in `avisados`.

## Risks

- `LinkedIn-Version` values are retired about a year after release; an expired one
  answers with an error status and R2.7 notifies it. Bump `versao` in config.
- An image may still be processing when the post is created; a token with only
  `w_member_social` cannot read the image status, so the post is sent right after the
  upload.
- A tick made while a run is rewriting the review file is lost; the box shows unticked
  afterwards, so it is visible.
