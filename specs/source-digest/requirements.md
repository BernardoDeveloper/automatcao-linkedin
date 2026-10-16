---
autonomy: auto
ci: wait
---

# Source digest — requirements

## Purpose

Bernardo's AI work is scattered across his second brain, ai-memory, his git repositories
and his Claude Code sessions. `linkedin coletar` gathers what changed in each source
during the window into one digest, so the drafts skill reads one file instead of four
places.

## R1 · Sources

- **R1.1** When `linkedin coletar` runs, the CLI shall collect the Markdown notes under the second brain modified during the window, excluding `.obsidian/`, `_templates/` and the drafts folder.
- **R1.2** When `linkedin coletar` runs, the CLI shall collect the ai-memory wiki pages modified during the window, excluding event logs (`log-*.md`) and scope manifests (`_meta.md`).
- **R1.3** When `linkedin coletar` runs, the CLI shall collect the subjects of commits authored by the configured email during the window, from every git repository directly under each configured repository root.
- **R1.4** When `linkedin coletar` runs, the CLI shall collect the prompts the user typed in Claude Code session transcripts during the window, excluding messages the harness generated.
- **R1.5** The CLI shall keep a note or an ai-memory page only when it contains at least the configured minimum number of AI keyword occurrences, and a session prompt only when it contains at least one, counting whole words outside URLs and ignoring case.
- **R1.6** If a configured source path does not exist, then the CLI shall skip that source and name it in the digest as skipped.

## R2 · Window

- **R2.1** The CLI shall start the window at the last successful run.
- **R2.2** Where `--desde AAAA-MM-DD` is given, the CLI shall start the window at that date instead.
- **R2.3** While no successful run is recorded, the CLI shall start the window the configured number of days ago.
- **R2.4** When the digest is written, the CLI shall record the run's start time as the last successful run.

## R3 · Digest

- **R3.1** The CLI shall write each run's digest to its own file, `dossies/AAAA-MM-DD-HHMMSS.md` under the repository, one section per source, each item with its date, its path or repository, and an excerpt no longer than the configured length.
- **R3.2** The CLI shall keep at most the configured number of items per source, the most recent first.
- **R3.3** When the digest is written, the CLI shall print its path.

## Out of scope

- Deciding which items deserve a post — that is the drafts skill (`specs/post-drafts/`).
