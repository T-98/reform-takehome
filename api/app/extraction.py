"""PDF extraction via OpenAI with validation and retry logic."""
import base64
import io
import json
import os
from typing import Optional
import fitz  # PyMuPDF
from openai import OpenAI
from pydantic import ValidationError

from .schemas import (
    RawExtractionOutput, ExtractionResponse, DocumentType,
    CanonicalField, Identifier, IdentifierType, Table, TableRow, LineItem
)
from .confidence import score_canonical_field, score_identifier, get_badge, compute_final_confidence

EXTRACTION_PROMPT = """You are a document extraction assistant specialized in logistics and trade documents.

TASK: Extract structured data from ALL provided page images. You will receive one or more images representing pages of a PDF document. You MUST analyze EVERY image/page and combine the extracted data into a single unified response.

CRITICAL INSTRUCTIONS:
1. IMPORTANT: Analyze ALL images provided. Each image is a separate page of the document. Extract data from EVERY page.
2. Documents vary in format; fields may be missing. Use null when a field is absent.
3. Do NOT invent or fabricate values. Only extract what is clearly visible.
4. Return ONLY valid JSON matching the schema below. No markdown, no explanation.
5. Tables may have NO visible borders or lines. You MUST infer columns from alignment, spacing, and repeated row patterns.
6. If table headers are missing or unclear, use col1, col2, col3, etc.
7. Preserve column order and row order exactly as they appear in the document.
8. If multiple tables exist across pages, combine rows into a single table if they share the same structure.
9. Provide model_confidence (0.0 to 1.0) for EVERY extracted value.

DOCUMENT TYPES:
- "BOL" for Bill of Lading
- "COMMERCIAL_INVOICE" for Commercial Invoice
- "PACKING_LIST" for Packing List
- "UNKNOWN" if document type is unclear

IDENTIFIER TYPES (use the most specific):
- BILL_OF_LADING: Main B/L number
- HOUSE_BOL_HBL: House Bill of Lading
- MASTER_BOL_MBL: Master Bill of Lading
- AIR_WAYBILL_AWB: Air Waybill number
- BOOKING_NUMBER: Booking/reservation number
- INVOICE_NUMBER: Invoice number
- DOCUMENT_NUMBER: Generic document number
- PO_NUMBER: Purchase Order number
- OTHER: Any other identifier

REQUIRED JSON SCHEMA:
{
  "document_type": "BOL" | "COMMERCIAL_INVOICE" | "PACKING_LIST" | "UNKNOWN",

  "bill_of_lading_number": "<string or null>",
  "bill_of_lading_number_confidence": <0.0-1.0>,

  "invoice_number": "<string or null>",
  "invoice_number_confidence": <0.0-1.0>,

  "shipper_name": "<string or null>",
  "shipper_name_confidence": <0.0-1.0>,

  "shipper_address": "<string or null>",
  "shipper_address_confidence": <0.0-1.0>,

  "consignee_name": "<string or null>",
  "consignee_name_confidence": <0.0-1.0>,

  "consignee_address": "<string or null>",
  "consignee_address_confidence": <0.0-1.0>,

  "total_value_of_goods": "<string or null>",
  "total_value_of_goods_confidence": <0.0-1.0>,

  "identifiers": [
    {"type": "<IDENTIFIER_TYPE>", "value": "<string>", "model_confidence": <0.0-1.0>}
  ],

  "tables": [
    {
      "table_id": "<unique_id>",
      "title": "<table title or null>",
      "headers": ["col1", "col2", ...],
      "rows": [
        {"cells": ["cell1", "cell2", ...], "row_confidence": <0.0-1.0>}
      ],
      "cell_confidence": [[<0.0-1.0>, ...], ...]
    }
  ],

  "line_items": [
    {
      "description": "<string or null>",
      "quantity": <number or null>,
      "unit": "<string or null>",
      "unit_value": <number or null>,
      "total_value": <number or null>,
      "hts_code": "<string or null>",
      "model_confidence": <0.0-1.0>
    }
  ] or null
}

Remember: Return ONLY the JSON object. No additional text."""

REPAIR_PROMPT_TEMPLATE = """The previous extraction attempt produced invalid JSON.

Validation errors:
{errors}

Please fix the JSON and return ONLY a valid JSON object matching the required schema.
Do not include any explanation or markdown formatting."""


class ExtractionService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_retries = 2

    def extract_from_pdf(self, pdf_bytes: bytes) -> ExtractionResponse:
        """Extract structured data from PDF with validation and retries."""
        # Convert PDF pages to images (OpenAI vision API only accepts images)
        page_images = self._pdf_to_images(pdf_bytes)
        print(f"[Extraction] Converted PDF to {len(page_images)} page image(s)")
        if not page_images:
            return ExtractionResponse(extraction_error="Failed to convert PDF to images")

        last_error: Optional[str] = None
        raw_output: Optional[RawExtractionOutput] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt == 0:
                    # First attempt
                    raw_json = self._call_openai(page_images, EXTRACTION_PROMPT)
                else:
                    # Repair attempt
                    repair_prompt = REPAIR_PROMPT_TEMPLATE.format(errors=last_error)
                    raw_json = self._call_openai(page_images, repair_prompt)

                # Parse and validate JSON
                raw_output = self._validate_raw_output(raw_json)
                break  # Success

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = str(e)
                if attempt == self.max_retries:
                    # All retries exhausted
                    return ExtractionResponse(
                        extraction_error=f"Failed to extract valid JSON after {self.max_retries + 1} attempts. Last error: {last_error}"
                    )

        if raw_output is None:
            return ExtractionResponse(extraction_error="Extraction failed: no output")

        # Transform raw output to final response with confidence scoring
        return self._transform_to_response(raw_output)

    def _pdf_to_images(self, pdf_bytes: bytes, max_pages: int = 5) -> list[str]:
        """Convert PDF pages to base64-encoded PNG images."""
        images: list[str] = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(min(len(doc), max_pages)):
                page = doc[page_num]
                # Render at 150 DPI for good quality without being too large
                mat = fitz.Matrix(150 / 72, 150 / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
                images.append(img_base64)
            doc.close()
        except Exception as e:
            print(f"PDF to image conversion failed: {e}")
            return []
        return images

    def _call_openai(self, page_images: list[str], prompt: str) -> str:
        """Call OpenAI API with page images and prompt."""
        # Build content with text prompt + all page images
        content: list[dict] = [{"type": "text", "text": prompt}]
        for img_base64 in page_images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"
                }
            })

        print(f"[Extraction] Sending {len(page_images)} image(s) to OpenAI")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
            temperature=0.1,
        )

        result = response.choices[0].message.content or ""
        # Strip markdown code blocks if present
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        return result.strip()

    def _validate_raw_output(self, raw_json: str) -> RawExtractionOutput:
        """Parse and validate raw JSON output."""
        data = json.loads(raw_json)
        return RawExtractionOutput.model_validate(data)

    def _transform_to_response(self, raw: RawExtractionOutput) -> ExtractionResponse:
        """Transform raw extraction to final response with confidence scoring."""

        def make_canonical_field(value: Optional[str], confidence: float, field_name: str) -> Optional[CanonicalField]:
            if value is None:
                return None
            final_conf, badge = score_canonical_field(field_name, value, confidence)
            return CanonicalField(
                value=value,
                model_confidence=confidence,
                final_confidence=final_conf,
                badge=badge
            )

        # Parse document type
        try:
            doc_type = DocumentType(raw.document_type)
        except ValueError:
            doc_type = DocumentType.UNKNOWN

        # Transform identifiers
        identifiers: list[Identifier] = []
        for id_data in raw.identifiers:
            try:
                id_type = IdentifierType(id_data.get("type", "OTHER"))
            except ValueError:
                id_type = IdentifierType.OTHER

            value = id_data.get("value", "")
            model_conf = float(id_data.get("model_confidence", 0.5))
            final_conf, badge = score_identifier(id_type.value, value, model_conf)

            identifiers.append(Identifier(
                type=id_type,
                value=value,
                model_confidence=model_conf,
                final_confidence=final_conf,
                badge=badge
            ))

        # Transform tables
        tables: list[Table] = []
        for idx, table_data in enumerate(raw.tables):
            rows: list[TableRow] = []
            for row_data in table_data.get("rows", []):
                # Convert null cells to empty strings
                raw_cells = row_data.get("cells", [])
                cells = [c if c is not None else "" for c in raw_cells]
                rows.append(TableRow(
                    cells=cells,
                    row_confidence=float(row_data.get("row_confidence", 0.5))
                ))

            # Convert null headers to empty strings
            raw_headers = table_data.get("headers", [])
            headers = [h if h is not None else "" for h in raw_headers]
            tables.append(Table(
                table_id=table_data.get("table_id", f"table_{idx}"),
                title=table_data.get("title"),
                headers=headers,
                rows=rows,
                cell_confidence=table_data.get("cell_confidence")
            ))

        # Transform line items
        line_items: Optional[list[LineItem]] = None
        if raw.line_items:
            line_items = []
            for item_data in raw.line_items:
                line_items.append(LineItem(
                    description=item_data.get("description"),
                    quantity=item_data.get("quantity"),
                    unit=item_data.get("unit"),
                    unit_value=item_data.get("unit_value"),
                    total_value=item_data.get("total_value"),
                    hts_code=item_data.get("hts_code"),
                    model_confidence=float(item_data.get("model_confidence", 0.5))
                ))

        return ExtractionResponse(
            document_type=doc_type,
            bill_of_lading_number=make_canonical_field(
                raw.bill_of_lading_number,
                raw.bill_of_lading_number_confidence,
                "bill_of_lading_number"
            ),
            invoice_number=make_canonical_field(
                raw.invoice_number,
                raw.invoice_number_confidence,
                "invoice_number"
            ),
            shipper_name=make_canonical_field(
                raw.shipper_name,
                raw.shipper_name_confidence,
                "shipper_name"
            ),
            shipper_address=make_canonical_field(
                raw.shipper_address,
                raw.shipper_address_confidence,
                "shipper_address"
            ),
            consignee_name=make_canonical_field(
                raw.consignee_name,
                raw.consignee_name_confidence,
                "consignee_name"
            ),
            consignee_address=make_canonical_field(
                raw.consignee_address,
                raw.consignee_address_confidence,
                "consignee_address"
            ),
            total_value_of_goods=make_canonical_field(
                raw.total_value_of_goods,
                raw.total_value_of_goods_confidence,
                "total_value_of_goods"
            ),
            identifiers=identifiers,
            tables=tables,
            line_items=line_items,
        )
