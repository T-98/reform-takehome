export type DocumentType = "BOL" | "COMMERCIAL_INVOICE" | "PACKING_LIST" | "UNKNOWN";

export type IdentifierType =
  | "BILL_OF_LADING"
  | "HOUSE_BOL_HBL"
  | "MASTER_BOL_MBL"
  | "AIR_WAYBILL_AWB"
  | "BOOKING_NUMBER"
  | "INVOICE_NUMBER"
  | "DOCUMENT_NUMBER"
  | "PO_NUMBER"
  | "OTHER";

export type ConfidenceBadge = "High" | "Med" | "Low";

export interface CanonicalField {
  value: string | null;
  model_confidence: number;
  final_confidence: number | null;
  badge: ConfidenceBadge | null;
}

export interface Identifier {
  type: IdentifierType;
  value: string;
  model_confidence: number;
  final_confidence: number | null;
  badge: ConfidenceBadge | null;
}

export interface TableRow {
  cells: string[];
  row_confidence: number;
}

export interface ExtractedTable {
  table_id: string;
  title: string | null;
  headers: string[];
  rows: TableRow[];
  cell_confidence: number[][] | null;
}

export interface LineItem {
  description: string | null;
  quantity: number | null;
  unit: string | null;
  unit_value: number | null;
  total_value: number | null;
  hts_code: string | null;
  model_confidence: number;
}

export interface ExtractionResponse {
  document_type: DocumentType;
  bill_of_lading_number: CanonicalField | null;
  invoice_number: CanonicalField | null;
  shipper_name: CanonicalField | null;
  shipper_address: CanonicalField | null;
  consignee_name: CanonicalField | null;
  consignee_address: CanonicalField | null;
  total_value_of_goods: CanonicalField | null;
  identifiers: Identifier[];
  tables: ExtractedTable[];
  line_items: LineItem[] | null;
  extraction_error: string | null;
}

export type UIState = "idle" | "processing" | "success" | "error";
