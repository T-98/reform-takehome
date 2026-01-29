# Changelog

## [1.0.4] - 2026-01-29

### Fixed

- **Multiple tables now extracted separately**: Documents with multiple tables (e.g., cargo table + charges table in BOLs) are now extracted as separate entries instead of being combined.
- **Column alignment normalized**: Rows with mismatched cell counts are now padded or merged to match header count.

### Changed

- Updated extraction prompt to explicitly keep tables separate (removed "combine tables" instruction)
- Added `_normalize_table_rows()` method to ensure row/header alignment
- 8 new unit tests for row normalization

## [1.0.3] - 2026-01-29

### Added
- **Continuation row merging for tables**: Description-only lines in tables (common in commercial invoices) are now merged with the previous row. For example, "148536001" + "SCREW 4.37" becomes "148536001 - SCREW 4.37".

### Changed
- Added `_is_continuation_row()` and `_merge_continuation_rows()` methods to ExtractionService
- 14 new unit tests for continuation row detection and merging

## [1.0.2] - 2026-01-29

### Fixed
- **Table cell validation error when OpenAI returns null values**: OpenAI sometimes returns `null` for empty table cells. The schema now allows nullable cells and the transformation converts nulls to empty strings.

## [1.0.1] - 2026-01-29

### Fixed
- **PDF extraction failing with "Invalid MIME type" error**: OpenAI's vision API only accepts images, not PDFs directly. The extraction service now converts PDF pages to PNG images before sending to OpenAI.

### Added
- `pymupdf>=1.24.0` dependency for PDF-to-image conversion
- `_pdf_to_images()` method in `ExtractionService` that renders PDF pages at 150 DPI
- Support for multi-page PDFs (up to 5 pages)

### Changed
- `_call_openai()` now accepts a list of base64-encoded PNG images instead of a single PDF
- MIME type changed from `application/pdf` to `image/png` in API requests

## [1.0.0] - 2026-01-29

### Added
- Initial implementation of document upload portal
- FastAPI backend with `/api/documents` endpoint for PDF extraction
- OpenAI gpt-4o vision API integration for OCR
- Flexible extraction schema with nullable fields for all document types
- Confidence scoring system (0.6 * heuristic + 0.4 * model_confidence)
- JSON validation with 2 retry attempts on invalid output
- Next.js frontend with shadcn/ui components
- PDF viewer using react-pdf with SSR compatibility
- Extraction results panel with confidence badges
- Support for BOL, Commercial Invoice, and Packing List documents
- Table extraction with support for borderless tables
