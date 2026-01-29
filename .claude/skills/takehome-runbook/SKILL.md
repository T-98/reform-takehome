---
name: takehome-runbook
summary: 4-hour execution loop. Prevent scope creep. Ship end-to-end first.
when_to_use:
  - start of assignment
  - whenever scope creeps
---

## Plan (default)
0:00–0:20  Prompt compression + acceptance criteria + “won’t do”
0:20–2:10  Vertical slice: upload → PDF viewer → OCR extraction → results JSON → render
2:10–3:00  Confidence scoring + table rendering + edge cases
3:00–4:00  Tests (minimal) + README + DECISIONS + polish

## Must-have checklist
- Upload one PDF
- Show PDF immediately
- Show extracted fields + identifiers + tables + confidence
- Skeleton while extracting; disable upload while extracting (Option A)
- README + DECISIONS.md

## “Won’t do” defaults
- No auth unless explicitly required
- No per-document templates
- No highlight overlays (confidence is enough)
- No background job system unless absolutely necessary