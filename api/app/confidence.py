"""Confidence scoring: final = 0.6*heuristic + 0.4*(model_confidence*100)."""
import re
from typing import Optional
from .schemas import ConfidenceBadge


def get_badge(final_confidence: int) -> ConfidenceBadge:
    """Return High/Med/Low badge based on final confidence score."""
    if final_confidence >= 80:
        return ConfidenceBadge.HIGH
    elif final_confidence >= 50:
        return ConfidenceBadge.MEDIUM
    return ConfidenceBadge.LOW


def compute_final_confidence(heuristic: float, model_confidence: float) -> int:
    """Compute final confidence: 0.6*heuristic + 0.4*(model_confidence*100)."""
    return round(0.6 * heuristic + 0.4 * (model_confidence * 100))


# --- Heuristic functions ---

def heuristic_invoice_number(value: Optional[str]) -> float:
    """Boost if value matches INV/INVOICE patterns."""
    if not value:
        return 0.0
    value_upper = value.upper()
    # Strong pattern: INV-123, INVOICE #123, etc.
    if re.search(r'INV(OICE)?[\s#\-:]*\d+', value_upper):
        return 95.0
    # Has digits (likely an invoice number)
    if re.search(r'\d{3,}', value):
        return 70.0
    return 40.0


def heuristic_bol_number(value: Optional[str]) -> float:
    """Boost if value matches B/L, BOL, Bill of Lading patterns."""
    if not value:
        return 0.0
    value_upper = value.upper()
    # Strong patterns
    if re.search(r'(B/?L|BOL|BILL\s*OF\s*LADING)[\s#\-:]*\w+', value_upper):
        return 95.0
    # Carrier prefixes (MAEU, HLCU, COSU, etc.) followed by numbers
    if re.search(r'^[A-Z]{4}\d{7,}', value_upper):
        return 90.0
    # Alphanumeric with reasonable length
    if re.search(r'^[A-Z0-9]{8,}$', value_upper):
        return 65.0
    return 40.0


def heuristic_address(value: Optional[str]) -> float:
    """Boost if value looks like an address (city/state/zip or street pattern)."""
    if not value:
        return 0.0
    # US ZIP pattern
    if re.search(r'\b\d{5}(-\d{4})?\b', value):
        return 90.0
    # State abbreviations
    if re.search(r'\b[A-Z]{2}\s+\d{5}', value.upper()):
        return 90.0
    # Street patterns
    if re.search(r'\b(street|st|ave|avenue|road|rd|blvd|drive|dr|lane|ln)\b', value.lower()):
        return 85.0
    # Has comma separators (city, state format)
    if ',' in value and len(value) > 10:
        return 70.0
    # Generic - has numbers and letters
    if re.search(r'\d+', value) and len(value) > 5:
        return 50.0
    return 30.0


def heuristic_currency_value(value: Optional[str]) -> float:
    """Boost if value is parseable as numeric/currency."""
    if not value:
        return 0.0
    # Currency symbols
    if re.search(r'[$€£¥][\d,]+\.?\d*', value):
        return 95.0
    # Plain number with decimals
    if re.search(r'^\d{1,3}(,\d{3})*(\.\d{2})?$', value.strip()):
        return 90.0
    # Just digits
    try:
        float(value.replace(',', '').replace('$', '').replace('€', ''))
        return 85.0
    except ValueError:
        pass
    return 30.0


def heuristic_name(value: Optional[str]) -> float:
    """Basic heuristic for company/person names."""
    if not value:
        return 0.0
    # Company suffixes
    if re.search(r'\b(LLC|INC|CORP|LTD|CO|COMPANY|INDUSTRIES|ENTERPRISES)\b', value.upper()):
        return 90.0
    # Has reasonable length and capitalization
    if len(value) > 3 and value[0].isupper():
        return 70.0
    return 50.0


def heuristic_hts_code(value: Optional[str]) -> float:
    """Boost HTS codes (digits or dotted patterns like 8471.30.0000)."""
    if not value:
        return 0.0
    # Full HTS format
    if re.match(r'^\d{4}\.\d{2}(\.\d{2,4})?$', value):
        return 95.0
    # Simplified digits only
    if re.match(r'^\d{6,10}$', value):
        return 80.0
    return 30.0


def heuristic_table_cell(value: str, column_idx: int, column_values: list[str]) -> float:
    """Table cell heuristic: numeric columns should be mostly numeric."""
    if not value or value.strip() == '':
        return 50.0

    # Check if this looks numeric
    is_numeric = bool(re.match(r'^[\d,.$€£¥\-\s]+$', value.strip()))

    # Check column consistency
    numeric_count = sum(
        1 for v in column_values
        if v and re.match(r'^[\d,.$€£¥\-\s]+$', v.strip())
    )
    total_non_empty = sum(1 for v in column_values if v and v.strip())

    if total_non_empty == 0:
        return 50.0

    numeric_ratio = numeric_count / total_non_empty

    # If column is mostly numeric
    if numeric_ratio > 0.7:
        if is_numeric:
            return 90.0
        else:
            return 40.0  # Penalize non-numeric in numeric column
    else:
        # Text column
        if len(value.strip()) > 2:
            return 75.0
        return 60.0


# --- Field-specific scoring ---

FIELD_HEURISTICS = {
    'bill_of_lading_number': heuristic_bol_number,
    'invoice_number': heuristic_invoice_number,
    'shipper_name': heuristic_name,
    'shipper_address': heuristic_address,
    'consignee_name': heuristic_name,
    'consignee_address': heuristic_address,
    'total_value_of_goods': heuristic_currency_value,
}


def score_canonical_field(field_name: str, value: Optional[str], model_confidence: float) -> tuple[int, ConfidenceBadge]:
    """Score a canonical field and return (final_confidence, badge)."""
    if value is None:
        return (0, ConfidenceBadge.LOW)

    heuristic_fn = FIELD_HEURISTICS.get(field_name, lambda x: 50.0)
    heuristic = heuristic_fn(value)
    final = compute_final_confidence(heuristic, model_confidence)
    return (final, get_badge(final))


def score_identifier(identifier_type: str, value: str, model_confidence: float) -> tuple[int, ConfidenceBadge]:
    """Score an identifier based on its type."""
    type_upper = identifier_type.upper()

    if 'BOL' in type_upper or 'BILL_OF_LADING' in type_upper or 'AWB' in type_upper:
        heuristic = heuristic_bol_number(value)
    elif 'INVOICE' in type_upper:
        heuristic = heuristic_invoice_number(value)
    elif 'PO' in type_upper or 'BOOKING' in type_upper:
        heuristic = max(heuristic_invoice_number(value), 60.0)  # Generic ID pattern
    else:
        heuristic = 60.0  # Default for OTHER

    final = compute_final_confidence(heuristic, model_confidence)
    return (final, get_badge(final))
