---
autonomy: auto
ci: wait
---

# Post drafts — requirements

## Purpose

Turn a digest, or the material of a talk, into LinkedIn drafts in Bernardo's second
brain, in his voice, ready for him to review and paste. Two skills write drafts —
`/linkedin-rascunhos` weekly from the digest, `/linkedin-apresentacao` after a talk —
and `linkedin fila` shows the queue.

## R1 · Draft format

- **R1.1** The drafts skills shall write each draft as one Markdown file in the drafts folder, named `AAAA-MM-DD - <título>.md` after its creation date.
- **R1.2** The drafts skills shall give each draft the frontmatter `tipo: publicacao`, `area: Carreira`, `plataforma: LinkedIn`, `criado`, `publicar_em`, `pilar`, `status`, `fontes`, `link` and `tags`, and the sections `## Post` and `## Checklist antes de postar`.
- **R1.3** The drafts skills shall write the post body in Brazilian Portuguese, following the voice guide.

## R2 · Weekly drafts

- **R2.1** When `/linkedin-rascunhos` runs, the skill shall run `linkedin coletar` and write between one and three drafts with status `rascunho`, each naming the digest items it came from in `fontes`.
- **R2.2** When `/linkedin-rascunhos` chooses themes, the skill shall skip a theme an existing draft already covers.
- **R2.3** If the digest holds no item worth a post, then the skill shall write no draft and say why.
- **R2.4** When a draft is written, the skill shall run `linkedin checar` on it and rewrite the post body until it passes.
- **R2.5** When drafts are written, the skill shall add one task to the second brain's `TAREFAS.md` to review them, linking each draft.

## R3 · Talk drafts

- **R3.1** When `/linkedin-apresentacao` runs with the material of a talk, the skill shall write one draft with pillar `apresentacao` saying who the audience was, what was taught and what the audience asked or found hard.
- **R3.2** If the material does not give the talk's date or audience, then the skill shall ask for them before writing.
- **R3.3** When the talk draft is written, the skill shall run `linkedin checar` on it and rewrite the post body until it passes.

## R4 · Queue

- **R4.1** When `linkedin fila` runs, the CLI shall list every draft in the drafts folder grouped by status, with its `publicar_em` and title.
- **R4.2** When `linkedin fila` runs, the CLI shall run the confidentiality check on every draft with status `rascunho` or `aprovado` and mark each one that fails.
- **R4.3** If a draft with status `aprovado` fails the confidentiality check, then the CLI shall exit with status 2.

## Out of scope

- Publishing, scheduling, carousels and images (plans/linkedin-conteudo-ia.md).
