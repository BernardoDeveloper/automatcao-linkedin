---
autonomy: auto
ci: no-wait
---

# Automatic publishing — requirements

## Purpose

Publish approved drafts to Bernardo's LinkedIn profile on their date, so he never opens
LinkedIn to post. He reviews in one Markdown file, ticks what may go out and drops
images in a folder; the only interruptions are desktop notifications. Supersedes the
"drafts only" decision (adr:0003-publish-approved-drafts-through-the-linkedin-api).

## R1 · Review file and approval

- **R1.1** When the publish run starts, the publisher shall rewrite the review file, listing every draft with status `rascunho` or `aprovado` with its `publicar_em`, its image and what still blocks it.
- **R1.2** The publisher shall list a draft awaiting review as an unticked checkbox and an approved draft as a ticked checkbox.
- **R1.3** When the checkbox of a draft awaiting review is ticked in the review file, the publisher shall record an approval bound to a fingerprint of the post body, the first comment and the image, and set the draft's status to `aprovado`.
- **R1.4** When the checkbox of an approved draft is unticked in the review file, the publisher shall drop its approval and set its status back to `rascunho`.
- **R1.5** If an approved draft's fingerprint no longer matches its approval, then the publisher shall drop the approval, set its status back to `rascunho` and notify that the draft changed after approval.
- **R1.6** If a draft has status `aprovado` without a recorded approval, then the publisher shall list it for review and shall not publish it.
- **R1.7** Where a draft lists people in `mencoes`, the publisher shall list it under manual publishing and shall not publish it.
- **R1.8** When a draft enters the review file for the first time, the publisher shall notify that a post awaits review.

## R2 · Publishing

- **R2.1** When the publish run finds an approved draft whose `publicar_em` is today, earlier or empty, the publisher shall publish its post body to Bernardo's profile, with its image when the draft names one.
- **R2.2** When a post is published, the publisher shall set the draft's status to `publicado`, fill `link` with the post's URL and notify.
- **R2.3** Where a published draft has `primeiro_comentario`, the publisher shall add it as a comment on the post.
- **R2.4** If the first comment is rejected, then the publisher shall keep the draft as `publicado` and notify to add the comment by hand.
- **R2.5** If an approved, due draft fails the confidentiality check, names an image that does not exist, or has an empty post body or one longer than 3000 characters, then the publisher shall not publish it and shall notify the reason once.
- **R2.6** The publisher shall send the post body in LinkedIn's commentary format, with reserved characters escaped and hashtags kept as hashtags.
- **R2.7** If LinkedIn refuses a publish request with a 4xx status, then the publisher shall keep the draft approved, notify the status and retry on the next run.
- **R2.8** If a publish request ends without an answer, with a 5xx status or with an unreadable answer, then the publisher shall not publish that draft again and shall notify to check LinkedIn by hand.
- **R2.9** When `linkedin publicar --simular` runs, the publisher shall print what it would approve and publish, and shall change no file and send no request.

## R3 · Access token

- **R3.1** When `linkedin login` runs, the CLI shall read a token pasted from LinkedIn's token generator without echoing it, look up the member it belongs to, and store both outside the repository, readable only by the user.
- **R3.2** The CLI shall never print the token nor write it anywhere but the token file.
- **R3.3** While the token expires in 7 days or less, the publisher shall notify once a day to run `linkedin login`.
- **R3.4** If there is no valid token, then the publisher shall publish nothing, keep rewriting the review file and notify once a day to run `linkedin login`.

## R4 · Schedule

- **R4.1** The scheduled publish run shall run every hour from 09:00 to 18:00, catching up a missed run, and after the weekly drafts run.
- **R4.2** While another publish run is in progress, the publisher shall exit without doing anything.

## Out of scope

- Mentioning people: the API needs a member's URN and offers no way to look one up, so
  drafts with `mencoes` stay manual.
- Editing or deleting published posts, video, documents, several images, polls.
- A time of day for a post: the first run on `publicar_em` publishes it.
