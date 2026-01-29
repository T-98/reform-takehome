---
name: backend-openai-ocr
summary: Backend contract for scanned PDF extraction via OpenAI. Flexible schema + generic tables + confidence scoring.
when_to_use:
  - implementing /api/documents
  - editing extraction prompt/schema
---

## Endpoint (sync)
POST /api/documents
- multipart: file (PDF)
- response: extracted JSON (one response, no polling)

## Output schema (must support missing fields)
Canonical fields (nullable):
- bill_of_lading_number: string | null
- invoice_number: string | null
- shipper_name: string | null
- shipper_address: string | null
- consignee_name: string | null
- consignee_address: string | null
- total_value_of_goods: number | null
- line_items: array | null (best-effort mapping only)

Flexibility:
- document_type: "BOL" | "COMMERCIAL_INVOICE" | "PACKING_LIST" | "UNKNOWN"
- identifiers: [{ type, value, model_confidence }]
  type enum includes (at minimum):
  - BILL_OF_LADING, HOUSE_BOL_HBL, MASTER_BOL_MBL, AIR_WAYBILL_AWB,
    BOOKING_NUMBER, INVOICE_NUMBER, DOCUMENT_NUMBER, PO_NUMBER, OTHER
- tables: [{ table_id, title, headers[], rows[], cell_confidence[][] }]
  rows: [{ cells[], row_confidence }]

## Extraction prompt (non-negotiable clauses)
Include ALL of these in the model instruction:
- “Documents vary; fields may be missing. Use null when absent.”
- “Do NOT invent values.”
- “Return ONLY valid JSON matching the schema.”
- “Tables may have NO visible borders/lines. Infer columns from alignment, spacing, and repeated row patterns.”
- “If headers are missing, use col1..colN.”
- “Preserve column order and row order.”
- “If multiple tables exist, extract the most relevant ‘items/commodities’ table; otherwise return tables: []”
- “Provide model_confidence (0–1) for each extracted value, including identifiers and table cells/rows.”

## Validation + retries
- Validate JSON strictly (schema/Pydantic).
- If invalid: retry up to 2 times with a “repair” prompt that includes validation error summary.
- If still invalid: return a safe error payload and HTTP 500/422.

## Confidence scoring (required)
Final confidence per field/cell:
- final = round(0.6*heuristic + 0.4*(model_confidence*100))
- badge: High>=80, Med 50–79, Low <50

Heuristics:
- Invoice number: labeled INV/INVOICE patterns boost
- BOL: B/L, BOL, Bill of Lading patterns boost
- HTS: digits or dotted pattern boost
- Currency values: parseable numeric/currency boost
- Addresses: city/state/zip or street pattern boosts
- Table consistency: numeric columns mostly numeric; penalize outliers

Line items mapping:
- Always return tables[].
- Populate canonical line_items[] only if you can confidently map qty/desc/value/hts from a table.
- Otherwise line_items = null (don’t force it).

## Env vars
- OPENAI_API_KEY
- OPENAI_MODEL (vision-capable; default to a reasonable model available in account)
- MAX_PAGES=5 (assumption)
- CORS_ORIGINS (comma-separated; include localhost)

## Output requirement
Whenever you modify backend, print:
- files changed
- how to run
- curl smoke test for /api/documents