---
autonomy: auto
ci: wait
---

# Confidentiality check — requirements

## Purpose

Drafts are written by a model from material that includes work at TOTVS. `linkedin
checar` is the mechanical gate between a draft and its approval: it finds the things
that must never reach a public post, so Bernardo's read can focus on tone instead of
hunting for an issue key.

## R1 · Findings

- **R1.1** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a Jira-style issue key such as `DJURPFS-1234`.
- **R1.2** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a Protheus source file name ending in `.prw`, `.prx`, `.tlpp`, `.aph` or `.ch`.
- **R1.3** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing an email address or an IPv4 address.
- **R1.4** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a URL whose host is, or is under, a configured internal domain.
- **R1.5** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a credential-shaped token: `sk-`, `ghp_`, `github_pat_`, `xox` or `AKIA` prefixes followed by a long key.
- **R1.6** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a configured forbidden term as a whole word, ignoring case and accents.
- **R1.7** If a post body is longer than 3000 characters, then the CLI shall report it.
- **R1.8** If a draft has no `## Post` section, then the CLI shall report it.
- **R1.9** Where allowed terms are configured, the CLI shall not report an issue key that is one of them.
- **R1.10** The CLI shall give each finding the file, the line number, the rule name and the matched text.

## R2 · Outcome

- **R2.1** If any finding is reported, then the CLI shall exit with status 2.
- **R2.2** When no finding is reported, the CLI shall exit with status 0.

## Out of scope

- Judging tone, claims or whether a customer is recognisable from context — that is
  Bernardo's read before `aprovado` (adr:0001-drafts-only-no-linkedin-api).
