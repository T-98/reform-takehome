"""Tests for continuation row merging in table extraction."""
import pytest
from unittest.mock import patch, MagicMock
from app.extraction import ExtractionService
from app.schemas import TableRow


class TestIsContinuationRow:
    """Tests for _is_continuation_row() detection logic."""

    def setup_method(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            self.service = ExtractionService()

    def test_continuation_row_true(self):
        """Row with text in first cell, empty rest is continuation."""
        cells = ["SCREW 4.37", "", "", ""]
        assert self.service._is_continuation_row(cells) is True

    def test_continuation_row_with_whitespace(self):
        """Row with whitespace-only cells is continuation."""
        cells = ["Description text", "  ", "", "   "]
        assert self.service._is_continuation_row(cells) is True

    def test_not_continuation_has_data(self):
        """Row with data in other columns is not continuation."""
        cells = ["148536001", "20", "7.91", "$158.10"]
        assert self.service._is_continuation_row(cells) is False

    def test_not_continuation_empty_first(self):
        """Row with empty first cell is not continuation."""
        cells = ["", "20", "7.91", "$158.10"]
        assert self.service._is_continuation_row(cells) is False

    def test_not_continuation_all_empty(self):
        """Completely empty row is not continuation."""
        cells = ["", "", "", ""]
        assert self.service._is_continuation_row(cells) is False

    def test_not_continuation_single_cell(self):
        """Single cell row is not continuation (no 'other' columns)."""
        cells = ["Some text"]
        assert self.service._is_continuation_row(cells) is False

    def test_not_continuation_empty_list(self):
        """Empty cells list is not continuation."""
        cells = []
        assert self.service._is_continuation_row(cells) is False


class TestMergeContinuationRows:
    """Tests for _merge_continuation_rows() merging logic."""

    def setup_method(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            self.service = ExtractionService()

    def test_merge_single_continuation(self):
        """Merge one continuation row into parent."""
        rows = [
            TableRow(cells=["148536001", "20", "7.91", "$158.10"], row_confidence=0.9),
            TableRow(cells=["SCREW 4.37", "", "", ""], row_confidence=0.8),
        ]
        merged = self.service._merge_continuation_rows(rows)

        assert len(merged) == 1
        assert merged[0].cells[0] == "148536001 - SCREW 4.37"
        assert merged[0].cells[1] == "20"
        assert merged[0].cells[2] == "7.91"
        assert merged[0].cells[3] == "$158.10"
        assert merged[0].row_confidence == 0.8  # Min of 0.9 and 0.8

    def test_merge_multiple_continuations(self):
        """Merge multiple consecutive continuation rows into parent."""
        rows = [
            TableRow(cells=["MODEL-A", "100", "$5.00", "$500.00"], row_confidence=0.9),
            TableRow(cells=["Line 1 description", "", "", ""], row_confidence=0.8),
            TableRow(cells=["Line 2 description", "", "", ""], row_confidence=0.7),
        ]
        merged = self.service._merge_continuation_rows(rows)

        assert len(merged) == 1
        assert merged[0].cells[0] == "MODEL-A - Line 1 description - Line 2 description"
        assert merged[0].row_confidence == 0.7  # Min of all

    def test_merge_alternating_rows(self):
        """Handle alternating data and continuation rows."""
        rows = [
            TableRow(cells=["148536001", "20", "7.91", "$158.10"], row_confidence=0.9),
            TableRow(cells=["SCREW 4.37", "", "", ""], row_confidence=0.85),
            TableRow(cells=["S02620401", "6", "1.04", "$6.21"], row_confidence=0.88),
            TableRow(cells=["THREAD TAKE-UP SPRING", "", "", ""], row_confidence=0.82),
        ]
        merged = self.service._merge_continuation_rows(rows)

        assert len(merged) == 2
        assert merged[0].cells[0] == "148536001 - SCREW 4.37"
        assert merged[0].cells[1] == "20"
        assert merged[1].cells[0] == "S02620401 - THREAD TAKE-UP SPRING"
        assert merged[1].cells[1] == "6"

    def test_no_continuation_rows(self):
        """No merging when no continuation rows exist."""
        rows = [
            TableRow(cells=["MODEL-A", "100", "$5.00", "$500.00"], row_confidence=0.9),
            TableRow(cells=["MODEL-B", "50", "$10.00", "$500.00"], row_confidence=0.85),
        ]
        merged = self.service._merge_continuation_rows(rows)

        assert len(merged) == 2
        assert merged[0].cells == ["MODEL-A", "100", "$5.00", "$500.00"]
        assert merged[1].cells == ["MODEL-B", "50", "$10.00", "$500.00"]

    def test_empty_rows_list(self):
        """Handle empty rows list."""
        merged = self.service._merge_continuation_rows([])
        assert merged == []

    def test_single_row(self):
        """Handle single row (nothing to merge)."""
        rows = [TableRow(cells=["MODEL-A", "100", "$5.00", "$500.00"], row_confidence=0.9)]
        merged = self.service._merge_continuation_rows(rows)

        assert len(merged) == 1
        assert merged[0].cells == ["MODEL-A", "100", "$5.00", "$500.00"]

    def test_first_row_is_continuation_style(self):
        """First row that looks like continuation stays as-is (no previous row)."""
        rows = [
            TableRow(cells=["Orphan description", "", "", ""], row_confidence=0.8),
            TableRow(cells=["MODEL-A", "100", "$5.00", "$500.00"], row_confidence=0.9),
        ]
        merged = self.service._merge_continuation_rows(rows)

        # First row stays as-is since there's no parent to merge into
        assert len(merged) == 2
        assert merged[0].cells[0] == "Orphan description"
        assert merged[1].cells[0] == "MODEL-A"
