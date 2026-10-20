---
status: superseded
superseded-by: 0003-publish-approved-drafts-through-the-linkedin-api
---

# 0001 · Drafts only, no LinkedIn API

## Context

Posts come from material that includes work at TOTVS: talks, internal tooling, issues.
A post that leaks an issue key, a customer name or a source file name cannot be
unpublished from people's feeds. LinkedIn's official API ("Share on LinkedIn",
`w_member_social`) needs a developer app, OAuth and token refresh; browser automation
breaks LinkedIn's terms and risks the account.

## Decision

The system writes drafts into the second brain and stops there. Bernardo reads each one,
moves it to `aprovado`, and pastes it into LinkedIn himself, then records the link and
sets `publicado`. Nothing in this repository holds LinkedIn credentials.

## Consequences

- Every post gets a human read, which is the last line of defence after the
  confidentiality check.
- Posting stays a manual two-minute step; the weekly run cannot schedule a post.
- Adding the API later is a new ADR superseding this one, plus an OAuth flow; the draft
  format already carries `publicar_em` and `link`, so the queue does not change.
