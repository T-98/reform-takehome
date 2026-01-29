"""Tests for schema validation."""
import pytest
from pydantic import ValidationError
from app.schemas import (
    RawExtractionOutput,
    ExtractionResponse,
    DocumentType,
    IdentifierType,
    CanonicalField,
    ConfidenceBadge,
)


class TestRawExtractionOutput:
    def test_minimal_valid_output(self):
        """Minimal valid output with all defaults."""
        data = {}
        output = RawExtractionOutput.model_validate(data)
        assert output.document_type == "UNKNOWN"
        assert output.bill_of_lading_number is None
        assert output.identifiers == []
        assert output.tables == []

    def test_full_valid_output(self):
        """Full valid output with all fields."""
        data = {
            "document_type": "BOL",
            "bill_of_lading_number": "MAEU123456789",
            "bill_of_lading_number_confidence": 0.95,
            "invoice_number": "INV-001",
            "invoice_number_confidence": 0.8,
            "shipper_name": "Acme Corp",
            "shipper_name_confidence": 0.9,
            "shipper_address": "123 Main St",
            "shipper_address_confidence": 0.85,
            "consignee_name": "Beta Inc",
            "consignee_name_confidence": 0.88,
            "consignee_address": "456 Oak Ave",
            "consignee_address_confidence": 0.82,
            "total_value_of_goods": "$10,000.00",
            "total_value_of_goods_confidence": 0.75,
            "identifiers": [
                {"type": "BOOKING_NUMBER", "value": "BK123", "model_confidence": 0.9}
            ],
            "tables": [
                {
                    "table_id": "table_0",
                    "title": "Line Items",
                    "headers": ["Description", "Qty", "Value"],
                    "rows": [
                        {"cells": ["Widget", "100", "$500"], "row_confidence": 0.85}
                    ],
                }
            ],
        }
        output = RawExtractionOutput.model_validate(data)
        assert output.document_type == "BOL"
        assert output.bill_of_lading_number == "MAEU123456789"
        assert len(output.identifiers) == 1
        assert len(output.tables) == 1

    def test_nullable_fields(self):
        """All canonical fields can be null."""
        data = {
            "document_type": "COMMERCIAL_INVOICE",
            "bill_of_lading_number": None,
            "invoice_number": None,
            "shipper_name": None,
            "consignee_name": None,
        }
        output = RawExtractionOutput.model_validate(data)
        assert output.bill_of_lading_number is None
        assert output.invoice_number is None

    def test_confidence_bounds(self):
        """Confidence must be between 0 and 1."""
        # Valid bounds
        data = {"bill_of_lading_number_confidence": 0.0}
        output = RawExtractionOutput.model_validate(data)
        assert output.bill_of_lading_number_confidence == 0.0

        data = {"bill_of_lading_number_confidence": 1.0}
        output = RawExtractionOutput.model_validate(data)
        assert output.bill_of_lading_number_confidence == 1.0

    def test_confidence_out_of_bounds(self):
        """Confidence outside 0-1 should fail validation."""
        with pytest.raises(ValidationError):
            RawExtractionOutput.model_validate({"bill_of_lading_number_confidence": 1.5})

        with pytest.raises(ValidationError):
            RawExtractionOutput.model_validate({"bill_of_lading_number_confidence": -0.1})


class TestExtractionResponse:
    def test_default_values(self):
        """Response with defaults."""
        response = ExtractionResponse()
        assert response.document_type == DocumentType.UNKNOWN
        assert response.bill_of_lading_number is None
        assert response.identifiers == []
        assert response.tables == []
        assert response.extraction_error is None

    def test_with_canonical_fields(self):
        """Response with canonical fields."""
        response = ExtractionResponse(
            document_type=DocumentType.BOL,
            bill_of_lading_number=CanonicalField(
                value="MAEU123",
                model_confidence=0.9,
                final_confidence=85,
                badge=ConfidenceBadge.HIGH,
            ),
        )
        assert response.document_type == DocumentType.BOL
        assert response.bill_of_lading_number is not None
        assert response.bill_of_lading_number.value == "MAEU123"
        assert response.bill_of_lading_number.badge == ConfidenceBadge.HIGH

    def test_error_response(self):
        """Response with extraction error."""
        response = ExtractionResponse(
            extraction_error="Failed to parse JSON after 3 attempts"
        )
        assert response.extraction_error is not None
        assert "JSON" in response.extraction_error


class TestDocumentType:
    def test_valid_types(self):
        assert DocumentType.BOL.value == "BOL"
        assert DocumentType.COMMERCIAL_INVOICE.value == "COMMERCIAL_INVOICE"
        assert DocumentType.PACKING_LIST.value == "PACKING_LIST"
        assert DocumentType.UNKNOWN.value == "UNKNOWN"


class TestIdentifierType:
    def test_all_identifier_types(self):
        """All expected identifier types exist."""
        expected = [
            "BILL_OF_LADING",
            "HOUSE_BOL_HBL",
            "MASTER_BOL_MBL",
            "AIR_WAYBILL_AWB",
            "BOOKING_NUMBER",
            "INVOICE_NUMBER",
            "DOCUMENT_NUMBER",
            "PO_NUMBER",
            "OTHER",
        ]
        actual = [t.value for t in IdentifierType]
        for exp in expected:
            assert exp in actual
