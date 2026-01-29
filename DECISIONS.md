# Decisions & Tradeoffs

## Core Architecture

1. **OpenAI Vision API for OCR**: Chose OpenAI's gpt-4o with vision capabilities over AWS Textract or Tesseract because:
   - Native PDF understanding without preprocessing
   - Better at inferring structure from scanned documents
   - Single API for both OCR and structured extraction
   - Avoids IAM/credential complexity in a 4-hour timebox

2. **Synchronous extraction (Option A UX)**: User waits for extraction to complete rather than polling.
   - Simpler implementation
   - PDF is shown immediately; skeleton indicates processing
   - Upload disabled during extraction prevents race conditions
   - Trade-off: Long PDFs may cause timeouts (mitigated by MAX_PAGES=5)

3. **FastAPI + Next.js**: Separate backend/frontend for clear separation of concerns.
   - FastAPI: Fast, typed Python with Pydantic validation
   - Next.js: Modern React with shadcn/ui for consistent styling
   - Could have been a single Next.js API route, but Python ecosystem for OpenAI is more mature

## Schema Design

4. **Flexible schema with nullable fields**: Canonical fields (BOL#, invoice#, shipper, consignee) are all nullable.
   - Documents vary widely; forcing non-null would cause extraction failures
   - `identifiers[]` captures additional references (HBL, MBL, AWB, booking#, PO#)
   - `tables[]` preserves raw table structure for any document type

5. **No hardcoded document templates**: The same prompt handles BOL, Commercial Invoice, Packing List, or unknown.
   - Document type is inferred, not required input
   - Avoids maintenance burden of per-type templates
   - Trade-off: Less precision than type-specific prompts

6. **Tables without borders**: Extraction prompt explicitly says "Tables may have NO visible borders/lines. Infer columns from alignment, spacing, and repeated row patterns."
   - Scanned logistics documents often have faded or missing table lines
   - Model is instructed to use col1..colN if headers are unclear

7. **Table row descriptions: MODEL NO. only (no merged descriptions)**: Commercial invoices often have item descriptions on continuation lines below the MODEL NO. We chose to keep only the MODEL NO. without merging descriptions.
   - **Why**: OpenAI returns clean, deterministic rows with just MODEL NO. + numeric values
   - **Trade-off**: Descriptions like "SCREW 4.37" or "THREAD TAKE-UP SPRING" are not captured
   - **Rationale given time constraint**:
     - Merging descriptions would require prompt engineering to get OpenAI to output them, which is non-deterministic
     - Current output is consistent and verifiable
     - Safety-net code exists (`_merge_continuation_rows()`) if OpenAI ever returns description-only rows
   - **Production improvement**: Could update prompt to explicitly request descriptions be appended to MODEL NO.

## Confidence Scoring

8. **Hybrid confidence**: `final = 0.6*heuristic + 0.4*(model_confidence*100)`
   - Model confidence alone is not calibrated for document extraction
   - Heuristics boost confidence when patterns match expectations:
     - INV/INVOICE prefix for invoice numbers
     - B/L, BOL, carrier codes for B/L numbers
     - ZIP codes, street patterns for addresses
     - Currency symbols, comma formatting for values

9. **High/Med/Low badges**: >=80 High, 50-79 Med, <50 Low
   - Simple visual indicator for users
   - Percentages shown for transparency

## Validation & Error Handling

10. **JSON validation with 2 retries**: If model output is invalid JSON, retry with a "repair" prompt.
   - OpenAI occasionally wraps JSON in markdown code blocks
   - Retry prompt includes validation error summary
   - After 2 retries, return HTTP 500 with error details

10. **Line items optional**: `line_items[]` is only populated if qty/desc/value can be confidently mapped from a table.
    - Otherwise remains null; raw `tables[]` preserves data
    - Avoids forcing incorrect mappings

## UI/UX

11. **Option A single-upload flow**: One PDF at a time, no queue.
    - Simpler state management
    - Clear visual feedback: idle → processing (skeleton) → success/error
    - "Upload New Document" button resets state

12. **shadcn/ui components**: Card, Button, Table, Badge, Skeleton, Alert.
    - Consistent, accessible design
    - Tailwind for layout only
    - No custom component styling

## Limitations

13. **No persistent storage**: Documents are processed in-memory only.
    - Production would use S3 + database
    - Listed as improvement in README

14. **No authentication**: Open endpoint for simplicity.
    - Production would add API key or OAuth
    - Can add simple X-API-Key header if needed

15. **No highlight overlays**: Confidence badges shown, but no bounding boxes on PDF.
    - Would require coordinate extraction from model
    - Listed as optional improvement
