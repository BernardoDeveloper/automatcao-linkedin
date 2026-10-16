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

- **R1.1** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a Jira-style issue key such as `PROJ-1234`, in any letter case, with the hyphen optionally surrounded by a space, or in uppercase with a space instead of the hyphen.
- **R1.2** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a Protheus source file name ending in `.prw`, `.prx`, `.tlpp`, `.aph` or `.ch`, or a user function name starting with `U_`.
- **R1.3** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing an email address or an IPv4 address.
- **R1.4** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a host that is, or is under, a configured internal domain, with or without a URL scheme and in any letter case.
- **R1.5** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a credential-shaped token: `sk-`, `ghp_`, `github_pat_`, `xox`, `AKIA`, `AIza`, `sk_live_` prefixes followed by a long key, a JWT, a private key header, a Slack webhook, or a `senha=`/`password:`/`token=` assignment.
- **R1.6** When `linkedin checar` runs on drafts, the CLI shall report each line of a post body containing a configured forbidden term as a whole word, ignoring case and accents, with any run of spaces, hyphens or underscores between its words and an optional plural `s` on each.
- **R1.7** If a post body is longer than 3000 characters, then the CLI shall report it.
- **R1.8** The CLI shall check every `## Post` section of a draft, and if a draft has none, then the CLI shall report it.
- **R1.9** Where allowed terms are configured, the CLI shall not report an issue key that is one of them.
- **R1.10** The CLI shall give each finding the file, the line number, the rule name and the matched text.
- **R1.11** The CLI shall match against each line after removing zero-width characters, applying NFKC normalization, reading every dash variant as a hyphen and reading `[.]` or `(.)` as a dot.
- **R1.12** If a pattern is split across two consecutive lines of a post body, then the CLI shall report it on the first of them.

## R2 · Outcome

- **R2.1** If any finding is reported, then the CLI shall exit with status 2.
- **R2.2** When no finding is reported, the CLI shall exit with status 0.
- **R2.3** If the forbidden terms or the internal domains are empty in config, then the CLI shall warn on stderr naming each empty list.

## Out of scope

- Judging tone, claims or whether a customer is recognisable from context — that is
  Bernardo's read before `aprovado` (adr:0001-drafts-only-no-linkedin-api).
