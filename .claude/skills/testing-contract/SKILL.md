---
name: testing-contract
summary: Minimal, high-signal tests under a hard timebox.
when_to_use:
  - writing tests
---

## Policy
Don’t do full TDD everywhere. Do a small suite that proves the backend contract.

## Minimum backend tests (4–6)
- POST /api/documents returns 200 and valid JSON schema for a sample PDF (mock OpenAI if possible)
- Validation: missing file → 422/400
- Error handling: OpenAI failure → returns error shape and non-200
- Schema validation path: invalid model JSON triggers retry logic (unit-test the retry function)

## Note
If mocking OpenAI is too time-consuming, test the schema validator + confidence scorer as pure functions and keep one “happy path” integration test behind a flag.