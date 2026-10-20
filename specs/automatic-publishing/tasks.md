# Automatic publishing — tasks

## 1 · Building blocks

- [x] 1.1 (Unit) Read the new config keys with their defaults, and add `post_body()` and `update()` to drafts — R1.1, R2.2
- [x] 1.2 (Unit) Convert a post body to LinkedIn's commentary format — R2.6
- [x] 1.3 (Unit) Send desktop notifications through notify-send, silent when it is missing — R1.8, R2.2
- [x] 1.4 (Unit) Call userinfo, image upload, post and comment over an injected transport — R2.1, R2.3, R3.1
- [x] 1.5 (Unit) Store, load and age the token file, and add `linkedin login` — R3.1, R3.2

## 2 · Review and publish

- [x] 2.1 (TDD) Read ticks, record and drop approvals bound to a fingerprint — R1.3, R1.4, R1.5, R1.6
- [x] 2.2 (Unit) Render the review file — R1.1, R1.2, R1.7
  _Depends 2.1_
- [x] 2.3 (TDD) Publish due approved drafts once, blocking failed checks and missing images, recording the link — R2.1, R2.2, R2.3, R2.4, R2.5, R2.7, R2.8
  _Depends 1.1, 1.2, 1.4, 2.1_
- [x] 2.4 (Unit) Notify once per draft and reason, token warnings once a day, and take the run lock — R1.8, R3.3, R3.4, R4.2
  _Depends 2.3_
- [x] 2.5 (Unit) Add `linkedin publicar [--simular]` to the CLI — R2.9
  _Depends 2.4, 2.2_

## 3 · Wiring

- [ ] 3.1 (Unit) Install the hourly publish timer and run the publisher after the weekly drafts — R4.1
- [ ] 3.2 (Unit) Teach the drafts skills and template the new frontmatter, drop the review task, document the flow — R1.7, R2.3
