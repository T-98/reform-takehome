---
name: quality-bar
summary: Final review checklist to maximize onsite pass rate.
when_to_use:
  - last 45 minutes
---

## Checklist
- README can run in 3 minutes (install, env, start, test upload)
- Clear env vars documented (OPENAI_API_KEY, model, CORS)
- Clear “Assumptions” and “Improvements”
- DECISIONS.md has 8–15 bullets: why OpenAI OCR, why sync, flexible schema, table strategy, confidence math, limitations
- UI has all states: idle/processing/success/error
- Output schema handles missing fields without hacks
- Prompt explicitly mentions “tables may have no borders” and “return only JSON”