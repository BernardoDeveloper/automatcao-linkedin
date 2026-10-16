# Confidentiality check — design

## What changes

Serves R1.1–R1.10, R2.1, R2.2.

`src/linkedin_ia/check.py`: `post_body(text) -> (start_line, body) | None` extracts the
`## Post` section (up to the next `## ` heading), and `check(path, config) ->
list[Finding]` runs each rule over it line by line. A rule is a name plus a compiled
pattern; forbidden terms and internal domains are compiled from config at call time.

Accent-insensitive matching (R1.6) folds the line and the term one character at a
time: `unicodedata.normalize("NFKD", c)` with combining marks dropped, kept only when
that leaves exactly one character. Folding is length-preserving, so a match span in the
folded line is the same span in the original, and the reported text is the original.

The issue-key pattern is `\b[A-Z][A-Z0-9]{1,9}-\d{1,6}\b`. It also matches harmless
uppercase-dash-number strings, such as `GPT-5` or `ISO-9001`, and that is accepted:
a false positive costs a rewrite, a miss costs a leak. Configured `permitidos`
(allowed terms) are removed from the line before the issue-key rule runs, so model
names can be whitelisted in config rather than in the draft.

## Risks

- A model may paraphrase an internal fact without any pattern in it. The check cannot
  see that; the human read can.
