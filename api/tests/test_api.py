"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.schemas import ExtractionResponse, DocumentType

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestDocumentsEndpoint:
    def test_missing_file(self):
        """POST without file returns 422."""
        response = client.post("/api/documents")
        assert response.status_code == 422

    def test_non_pdf_file(self):
        """POST with non-PDF returns 422."""
        response = client.post(
            "/api/documents",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 422
        assert "PDF" in response.json()["detail"]

    def test_empty_file(self):
        """POST with empty file returns 422."""
        response = client.post(
            "/api/documents",
            files={"file": ("test.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 422
        assert "Empty" in response.json()["detail"]

    @patch("app.main.extraction_service.extract_from_pdf")
    def test_successful_extraction(self, mock_extract):
        """POST with valid PDF returns extraction result."""
        mock_extract.return_value = ExtractionResponse(
            document_type=DocumentType.BOL,
        )

        # Minimal valid PDF header
        pdf_content = b"%PDF-1.4\n"

        response = client.post(
            "/api/documents",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "BOL"
        mock_extract.assert_called_once()

    @patch("app.main.extraction_service.extract_from_pdf")
    def test_extraction_error(self, mock_extract):
        """Extraction error returns 500."""
        mock_extract.return_value = ExtractionResponse(
            extraction_error="Failed to extract valid JSON after 3 attempts"
        )

        pdf_content = b"%PDF-1.4\n"

        response = client.post(
            "/api/documents",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )

        assert response.status_code == 500
        assert "JSON" in response.json()["detail"]

    @patch("app.main.extraction_service.extract_from_pdf")
    def test_extraction_exception(self, mock_extract):
        """Exception during extraction returns 500."""
        mock_extract.side_effect = Exception("OpenAI API error")

        pdf_content = b"%PDF-1.4\n"

        response = client.post(
            "/api/documents",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )

        assert response.status_code == 500
        assert "OpenAI" in response.json()["detail"]
