# Confidentiality check — design

## What changes

Serves R1.1–R1.12, R2.1–R2.3.

`src/linkedin_ia/check.py`: `post_bodies(text)` extracts every `## Post` section (each up
to the next `## ` heading), and `check(path, config) -> list[Finding]` runs each rule over
them line by line. A rule is a name plus a compiled pattern; forbidden terms and internal
domains are compiled from config at call time.

Every line is normalized first (R1.11), so findings report the normalized text. A pattern
split by a line break is found by matching each line joined to the next with a space and
keeping only the matches that cross the join (R1.12). Only the post body is checked: the
rest of a draft (`## Resumo`, frontmatter) is a private note that never leaves the second
brain.

The model writes the drafts after reading untrusted text, so the patterns aim at leaks
that survive reformatting, not only at the canonical form. Lookalike scripts (a Cyrillic
`а` in a customer name) are not covered; that is left to the human read.

Accent-insensitive matching (R1.6) folds the line and the term one character at a
time: `unicodedata.normalize("NFKD", c)` with combining marks dropped, kept only when
that leaves exactly one character. Folding is length-preserving, so a match span in the
folded line is the same span in the original, and the reported text is the original.

Issue keys are three patterns (R1.1). Uppercase tolerates reformatting; lowercase needs a
plain hyphen and three digits, because "top-10", "Etapa - 1" and "llama-3" are ordinary
prose in an AI post and every false positive costs the model a rewrite. Uppercase strings
such as `GPT-5` or `ISO-9001` still match, and that is accepted: a miss costs a leak. Configured `permitidos` (allowed terms) are
masked, ignoring case, before the issue-key rule runs, so model names can be whitelisted
in config rather than in the draft.

Internal domains match as bare hosts, not only inside `http(s)://` URLs: a host is a
dot-separated run that ends in the configured domain and is not followed by another
label, so `intranet.empresa.com.` at the end of a sentence matches and
`intranet.empresa.com.evil.io` does not.

## Risks

- A model may paraphrase an internal fact without any pattern in it. The check cannot
  see that; the human read can.
