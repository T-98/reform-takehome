"""Extraction response schema with nullable fields and confidence scoring."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    BOL = "BOL"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    PACKING_LIST = "PACKING_LIST"
    UNKNOWN = "UNKNOWN"


class IdentifierType(str, Enum):
    BILL_OF_LADING = "BILL_OF_LADING"
    HOUSE_BOL_HBL = "HOUSE_BOL_HBL"
    MASTER_BOL_MBL = "MASTER_BOL_MBL"
    AIR_WAYBILL_AWB = "AIR_WAYBILL_AWB"
    BOOKING_NUMBER = "BOOKING_NUMBER"
    INVOICE_NUMBER = "INVOICE_NUMBER"
    DOCUMENT_NUMBER = "DOCUMENT_NUMBER"
    PO_NUMBER = "PO_NUMBER"
    OTHER = "OTHER"


class ConfidenceBadge(str, Enum):
    HIGH = "High"
    MEDIUM = "Med"
    LOW = "Low"


class Identifier(BaseModel):
    type: IdentifierType
    value: str
    model_confidence: float = Field(ge=0, le=1)
    final_confidence: Optional[int] = None
    badge: Optional[ConfidenceBadge] = None


class TableRow(BaseModel):
    cells: list[Optional[str]]  # Allow null cells from model output
    row_confidence: float = Field(ge=0, le=1, default=0.5)


class Table(BaseModel):
    table_id: str
    title: Optional[str] = None
    headers: list[str]
    rows: list[TableRow]
    cell_confidence: Optional[list[list[float]]] = None


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_value: Optional[float] = None
    total_value: Optional[float] = None
    hts_code: Optional[str] = None
    model_confidence: float = Field(ge=0, le=1)


class CanonicalField(BaseModel):
    value: Optional[str] = None
    model_confidence: float = Field(ge=0, le=1, default=0.0)
    final_confidence: Optional[int] = None
    badge: Optional[ConfidenceBadge] = None


class ExtractionResponse(BaseModel):
    """Full extraction response with canonical fields, identifiers, and tables."""
    document_type: DocumentType = DocumentType.UNKNOWN

    # Canonical fields (all nullable)
    bill_of_lading_number: Optional[CanonicalField] = None
    invoice_number: Optional[CanonicalField] = None
    shipper_name: Optional[CanonicalField] = None
    shipper_address: Optional[CanonicalField] = None
    consignee_name: Optional[CanonicalField] = None
    consignee_address: Optional[CanonicalField] = None
    total_value_of_goods: Optional[CanonicalField] = None

    # Flexible fields
    identifiers: list[Identifier] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    line_items: Optional[list[LineItem]] = None

    # Metadata
    extraction_error: Optional[str] = None


class RawExtractionOutput(BaseModel):
    """Schema for validating raw model output before confidence scoring."""
    document_type: str = "UNKNOWN"

    bill_of_lading_number: Optional[str] = None
    bill_of_lading_number_confidence: float = Field(ge=0, le=1, default=0.0)

    invoice_number: Optional[str] = None
    invoice_number_confidence: float = Field(ge=0, le=1, default=0.0)

    shipper_name: Optional[str] = None
    shipper_name_confidence: float = Field(ge=0, le=1, default=0.0)

    shipper_address: Optional[str] = None
    shipper_address_confidence: float = Field(ge=0, le=1, default=0.0)

    consignee_name: Optional[str] = None
    consignee_name_confidence: float = Field(ge=0, le=1, default=0.0)

    consignee_address: Optional[str] = None
    consignee_address_confidence: float = Field(ge=0, le=1, default=0.0)

    total_value_of_goods: Optional[str] = None
    total_value_of_goods_confidence: float = Field(ge=0, le=1, default=0.0)

    identifiers: list[dict] = Field(default_factory=list)
    tables: list[dict] = Field(default_factory=list)
    line_items: Optional[list[dict]] = None
