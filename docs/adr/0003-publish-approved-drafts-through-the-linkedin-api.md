---
status: accepted
---

# 0003 · Publish approved drafts through the LinkedIn API

## Context

adr:0001-drafts-only-no-linkedin-api kept posting manual so every post got a human read.
Bernardo wants to stop pasting posts by hand: review in one place, get a desktop
notification, and let the system post on the planned day. The weekly drafts agent reads
untrusted text and can write drafts, so whatever marks a draft as approved must be out
of its reach. Browser automation still breaks LinkedIn's terms.

## Decision

Approved drafts are published through LinkedIn's official API ("Share on LinkedIn",
`w_member_social`; Posts, Images and Comments endpoints) by `linkedin publicar`, run by a
systemd user timer.

- Approval is a ticked checkbox in a review file outside the drafts folder, recorded in
  `.estado/` with a fingerprint of the post body, first comment and image. A draft that
  changes after approval goes back to review. A `status: aprovado` written into a draft
  approves nothing.
- The access token is pasted from the Developer Portal's token generator and kept in a
  `0600` file outside the repository. Nothing in the repository holds it.
- The confidentiality check runs again right before each post.
- Posts that mention people stay manual: the API cannot look up a member's URN.

## Consequences

- The human read stays, moved from LinkedIn to the review file.
- Every 60 days Bernardo pastes a new token (`linkedin login`); a notification warns a
  week ahead.
- A post goes out at the first run on its `publicar_em`, while the machine is on.
- `LinkedIn-Version` must be bumped about once a year.
