# Confidentiality check — tasks

## 1 · Check

- [x] 1.1 (TDD) Extract the post body and match each rule line by line, accent-folded terms and allowed terms included — R1.1, R1.2, R1.3, R1.4, R1.5, R1.6, R1.7, R1.8, R1.9, R1.10
- [x] 1.2 (Unit) Wire `linkedin checar` with exit status 2 on findings — R2.1, R2.2
  _Depends 1.1_

## 2 · Review fixes

- [x] 2.1 (TDD) Normalize lines, catch reformatted issue keys, bare internal hosts, wider credentials, U_ functions, split lines and every Post section — R1.1, R1.2, R1.4, R1.5, R1.6, R1.8, R1.11, R1.12
  _Reason security and code review findings_
- [x] 2.2 (Unit) Warn on stderr when forbidden terms or internal domains are empty — R2.3
  _Reason security review finding_
- [x] 2.3 (TDD) Keep ordinary prose clean: narrower any-case keys, spaced allowed terms, credential assignments with a digit — R1.1, R1.5, R1.9
  _Reason re-review finding_
