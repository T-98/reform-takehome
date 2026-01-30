# Document Upload Portal

A web portal for uploading scanned PDFs and extracting structured data using OpenAI's vision capabilities.

## Quick Start (3 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### 1. Backend Setup

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (already set up with provided API key)
# Edit .env if needed:
# OPENAI_API_KEY=your-key
# OPENAI_MODEL=gpt-4o
# CORS_ORIGINS=http://localhost:3000

# Start server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 3. Test Upload

1. Open http://localhost:3000
2. Upload a scanned PDF (Bill of Lading, Commercial Invoice, or Packing List)
3. View the PDF on the left, extracted data on the right

### Smoke Test (curl)

```bash
curl -X POST http://localhost:8000/api/documents \
  -F "file=@sample.pdf" \
  | jq .
```

## Environment Variables

### Backend (`api/.env`)
| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | Vision-capable model | `gpt-4o` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `MAX_PAGES` | Max pages to process | `5` |

### Frontend (`web/.env.local`)
| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│  FastAPI Backend │────▶│   OpenAI API    │
│   (Port 3000)   │     │   (Port 8000)    │     │   (gpt-4o)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Backend (`/api`)
- **FastAPI** for the REST API
- **OpenAI** for PDF vision extraction (base64-encoded PDF → structured JSON)
- **Pydantic** for schema validation with retry logic
- **Confidence scoring**: `final = 0.6*heuristic + 0.4*(model_confidence*100)`

### Frontend (`/web`)
- **Next.js 15** with App Router
- **TanStack Query** for data fetching (useMutation for extraction)
- **shadcn/ui** components (Card, Button, Table, Badge, Skeleton, Alert)
- **react-pdf** for PDF rendering

## API Endpoints

### `POST /api/documents`

Upload a PDF and extract structured data.

**Request:** `multipart/form-data` with `file` field (PDF)

**Response:**
```json
{
  "document_type": "BOL",
  "bill_of_lading_number": {
    "value": "MAEU123456789",
    "model_confidence": 0.95,
    "final_confidence": 95,
    "badge": "High"
  },
  "shipper_name": { ... },
  "consignee_name": { ... },
  "identifiers": [
    { "type": "BOOKING_NUMBER", "value": "BK123", "badge": "Med" }
  ],
  "tables": [
    {
      "table_id": "table_0",
      "headers": ["Description", "Qty", "Weight"],
      "rows": [{ "cells": ["Electronics", "100", "500kg"], "row_confidence": 0.9 }]
    }
  ]
}
```

### `GET /health`

Health check endpoint.

## Assumptions

1. **Single-page extraction**: PDFs are assumed to be 1-5 pages. Longer documents may truncate.
2. **Scanned PDFs**: The extraction prompt is optimized for scanned documents without text layers.
3. **Sync processing**: Extraction happens synchronously (Option A UX). No background jobs.
4. **In-memory**: No persistent storage. Documents are not saved after extraction.
5. **Tables without borders**: The prompt explicitly instructs the model to infer columns from alignment.

## Improvements (If More Time)

1. **Async processing**: Background jobs with polling for large documents
2. **Persistent storage**: S3 for PDFs, PostgreSQL for results
3. **Multi-page navigation**: Show all pages with thumbnails
4. **Highlight overlays**: Show bounding boxes for extracted fields on the PDF
5. **Document history**: List of previously processed documents
6. **Authentication**: API key or OAuth for production
7. **Caching**: Cache extraction results by file hash
8. **Better error handling**: Granular error codes, retry with exponential backoff
9. **Table item descriptions**: Currently only MODEL NO. is captured; descriptions on continuation lines (e.g., "SCREW 4.37") could be merged via prompt engineering

## BUGS
1. After adding heuristics for multi-table extraction and multi-line row merging, the OpenAI vision extraction became unstable: fixes for one document type regress others (tables get mis-selected, columns shift, or rows collapse).

## Key Assumption (Production vs. Take-home)

In this take-home, I’m using a single general-purpose vision model + carefully written prompts to handle *both* table detection (including borderless tables) and multi-line row merging. This works, but it’s inherently less stable — prompt changes that fix one PDF can regress another.

In a real production environment, I would **not** rely on prompt engineering alone for document structure.

### How I’d address this in production

- **Two-stage pipeline (more deterministic):**  
  Use a dedicated OCR + layout/table detection engine first, then use an LLM only to map the extracted structure into our canonical schema.

- **Specialized parsers for structure:**  
  Table boundaries, columns, and reading order should come from a layout engine (with bounding boxes), not from the LLM “guessing” structure.

- **Lightweight document routing:**  
  Even if we keep a single output schema, I’d classify documents (invoice vs B/L vs packing list) and route to the best extractor strategy for that type.

- **Confidence that isn’t just “model vibes”:**  
  Prefer OCR/layout engine confidences + deterministic validations over LLM self-reported confidence.

- **Regression harness (non-negotiable):**  
  Maintain a small corpus of representative PDFs with expected outputs and run automated regression tests on every change so fixes don’t break other formats.

- **Human-in-the-loop for ambiguous cases:**  
  When confidence is low or structure is unclear, surface it for review instead of forcing a best guess.

- **Better observability:**  
  Log key parsing decisions (table selected, rows merged, column normalization applied) so failures are diagnosable and not “prompt magic.”

## Testing

```bash
cd api
pytest -v
```

See [DECISIONS.md](./DECISIONS.md) for key tradeoffs.
