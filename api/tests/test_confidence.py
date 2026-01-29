"""Tests for confidence scoring functions."""
import pytest
from app.confidence import (
    compute_final_confidence,
    get_badge,
    heuristic_invoice_number,
    heuristic_bol_number,
    heuristic_address,
    heuristic_currency_value,
    heuristic_name,
    score_canonical_field,
    score_identifier,
)
from app.schemas import ConfidenceBadge


class TestComputeFinalConfidence:
    def test_full_confidence(self):
        # 0.6 * 100 + 0.4 * 100 = 100
        assert compute_final_confidence(100.0, 1.0) == 100

    def test_zero_confidence(self):
        assert compute_final_confidence(0.0, 0.0) == 0

    def test_mixed_confidence(self):
        # 0.6 * 80 + 0.4 * 90 = 48 + 36 = 84
        assert compute_final_confidence(80.0, 0.9) == 84

    def test_heuristic_weighted_higher(self):
        # Heuristic is weighted 0.6, model 0.4
        # 0.6 * 100 + 0.4 * 0 = 60
        assert compute_final_confidence(100.0, 0.0) == 60


class TestGetBadge:
    def test_high_badge(self):
        assert get_badge(80) == ConfidenceBadge.HIGH
        assert get_badge(95) == ConfidenceBadge.HIGH
        assert get_badge(100) == ConfidenceBadge.HIGH

    def test_medium_badge(self):
        assert get_badge(50) == ConfidenceBadge.MEDIUM
        assert get_badge(65) == ConfidenceBadge.MEDIUM
        assert get_badge(79) == ConfidenceBadge.MEDIUM

    def test_low_badge(self):
        assert get_badge(0) == ConfidenceBadge.LOW
        assert get_badge(25) == ConfidenceBadge.LOW
        assert get_badge(49) == ConfidenceBadge.LOW


class TestHeuristicInvoiceNumber:
    def test_strong_invoice_pattern(self):
        assert heuristic_invoice_number("INV-12345") == 95.0
        assert heuristic_invoice_number("INVOICE #67890") == 95.0
        assert heuristic_invoice_number("Invoice: 123") == 95.0

    def test_digits_only(self):
        assert heuristic_invoice_number("123456789") == 70.0

    def test_no_pattern(self):
        assert heuristic_invoice_number("ABC") == 40.0

    def test_none_value(self):
        assert heuristic_invoice_number(None) == 0.0


class TestHeuristicBolNumber:
    def test_bol_pattern(self):
        assert heuristic_bol_number("B/L 123456") == 95.0
        assert heuristic_bol_number("BOL-ABC123") == 95.0

    def test_carrier_code_pattern(self):
        # MAEU + 7+ digits = carrier prefix pattern
        assert heuristic_bol_number("MAEU1234567") == 90.0
        assert heuristic_bol_number("HLCU9876543") == 90.0

    def test_alphanumeric_pattern(self):
        assert heuristic_bol_number("ABCD12345678") >= 65.0

    def test_none_value(self):
        assert heuristic_bol_number(None) == 0.0


class TestHeuristicAddress:
    def test_us_zip(self):
        assert heuristic_address("123 Main St, City, CA 90210") == 90.0

    def test_street_pattern(self):
        assert heuristic_address("456 Oak Avenue") == 85.0

    def test_city_state_format(self):
        assert heuristic_address("Los Angeles, California") == 70.0

    def test_none_value(self):
        assert heuristic_address(None) == 0.0


class TestHeuristicCurrencyValue:
    def test_currency_symbol(self):
        assert heuristic_currency_value("$1,234.56") == 95.0
        assert heuristic_currency_value("€500.00") == 95.0

    def test_formatted_number(self):
        assert heuristic_currency_value("1,234.56") == 90.0

    def test_plain_number(self):
        assert heuristic_currency_value("1234.56") == 85.0

    def test_none_value(self):
        assert heuristic_currency_value(None) == 0.0


class TestHeuristicName:
    def test_company_suffix(self):
        assert heuristic_name("Acme Corp") == 90.0
        assert heuristic_name("Smith Industries LLC") == 90.0

    def test_capitalized_name(self):
        assert heuristic_name("John Smith") == 70.0

    def test_none_value(self):
        assert heuristic_name(None) == 0.0


class TestScoreCanonicalField:
    def test_invoice_number_high_confidence(self):
        final, badge = score_canonical_field("invoice_number", "INV-12345", 0.95)
        assert final >= 80
        assert badge == ConfidenceBadge.HIGH

    def test_none_value_low_confidence(self):
        final, badge = score_canonical_field("shipper_name", None, 0.0)
        assert final == 0
        assert badge == ConfidenceBadge.LOW


class TestScoreIdentifier:
    def test_bol_identifier(self):
        final, badge = score_identifier("BILL_OF_LADING", "MAEU1234567", 0.9)
        assert final >= 70
        assert badge in [ConfidenceBadge.HIGH, ConfidenceBadge.MEDIUM]

    def test_invoice_identifier(self):
        final, badge = score_identifier("INVOICE_NUMBER", "INV-999", 0.85)
        assert final >= 70
