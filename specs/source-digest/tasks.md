# Source digest — tasks

## 1 · Collect

- [x] 1.1 (Unit) Load config.toml with the example as fallback — R1.6, R2.3, R3.1, R3.2
- [x] 1.2 (Unit) Collect second brain notes and ai-memory pages by mtime and keyword — R1.1, R1.2, R1.5
  _Depends 1.1_
- [x] 1.3 (Unit) Collect commit subjects per repository under each root — R1.3
  _Depends 1.1_
- [x] 1.4 (Unit) Collect typed prompts from Claude Code transcripts — R1.4, R1.5
  _Depends 1.1_

## 2 · Digest

- [x] 2.1 (Unit) Resolve the window from state, `--desde` or the default — R2.1, R2.2, R2.3
  _Depends 1.1_
- [x] 2.2 (Unit) Render the digest, record the run and wire `linkedin coletar` — R1.6, R2.4, R3.1, R3.2, R3.3
  _Depends 1.2, 1.3, 1.4, 2.1_

## 3 · Review fixes

- [x] 3.1 (Unit) Give each run its own digest file and flatten origins — R3.1
  _Reason code review finding_
- [x] 3.2 (Unit) Count mentions in the body only, read transcripts defensively in local time, match the author email literally — R1.3, R1.4, R1.5
  _Reason code review finding_
- [x] 3.3 (Unit) Resolve the session folder name from the home path the way Claude Code writes it — R1.4
  _Reason re-review finding_
