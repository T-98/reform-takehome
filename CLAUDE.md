# Reform Take-home (4h) — Document Upload Portal

Use Skills for all procedural work. Do not expand scope. Build the thinnest vertical slice first.

Routing:
- Timeboxing, sequencing, submission checklist → .claude/skills/takehome-runbook/SKILL.md
- Backend OCR + extraction (OpenAI) + schema + confidence → .claude/skills/backend-openai-ocr/SKILL.md
- Frontend portal (Option A UX + Suspense Query patterns) → .claude/skills/takehome-frontend/SKILL.md
- Minimal tests (contract-first) → .claude/skills/testing-contract/SKILL.md
- Final review checklist + README/DECISIONS → .claude/skills/quality-bar/SKILL.md

Non-negotiables:
- Fields may be missing → output schema must allow nulls.
- Tables may have no borders → extraction prompt must say this explicitly.
- Confidence scores are required; highlighting is optional.