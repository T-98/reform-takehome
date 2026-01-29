"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ExtractionResponse,
  CanonicalField,
  Identifier,
  ExtractedTable,
  ConfidenceBadge,
  UIState,
} from "@/lib/types";

interface ExtractionPanelProps {
  state: UIState;
  data: ExtractionResponse | null;
  error: string | null;
  onRetry?: () => void;
}

function ConfidenceBadgeComponent({ badge }: { badge: ConfidenceBadge | null }) {
  if (!badge) return null;

  const variant =
    badge === "High" ? "default" : badge === "Med" ? "secondary" : "destructive";

  return (
    <Badge variant={variant} className="ml-2 text-xs">
      {badge}
    </Badge>
  );
}

function FieldRow({
  label,
  field,
}: {
  label: string;
  field: CanonicalField | null;
}) {
  if (!field || !field.value) {
    return (
      <div className="flex justify-between py-2">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-muted-foreground italic">Not found</span>
      </div>
    );
  }

  return (
    <div className="flex justify-between py-2 gap-4">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <div className="text-right">
        <span className="break-words">{field.value}</span>
        <ConfidenceBadgeComponent badge={field.badge} />
        {field.final_confidence !== null && (
          <span className="text-xs text-muted-foreground ml-1">
            ({field.final_confidence}%)
          </span>
        )}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardContent className="flex-1 space-y-6 overflow-y-auto">
        <div className="space-y-3">
          <Skeleton className="h-4 w-24" />
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex justify-between">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-40" />
            </div>
          ))}
        </div>
        <Separator />
        <div className="space-y-3">
          <Skeleton className="h-4 w-36" />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
        <Separator />
        <div className="space-y-3">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-32 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

function IdlePanel() {
  return (
    <Card className="h-full flex items-center justify-center bg-muted/50">
      <CardContent className="text-center text-muted-foreground">
        <p>Upload a PDF to extract data</p>
      </CardContent>
    </Card>
  );
}

function ErrorPanel({
  error,
  onRetry,
}: {
  error: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="h-full flex flex-col">
      <CardContent className="flex-1 p-6 overflow-y-auto">
        <Alert variant="destructive">
          <AlertTitle>Extraction Failed</AlertTitle>
          <AlertDescription className="mt-2">
            {error}
            {onRetry && (
              <button
                onClick={onRetry}
                className="block mt-3 underline hover:no-underline"
              >
                Try again
              </button>
            )}
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}

function IdentifiersSection({ identifiers }: { identifiers: Identifier[] }) {
  if (identifiers.length === 0) {
    return (
      <p className="text-muted-foreground italic text-sm">
        No additional identifiers found
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {identifiers.map((id, idx) => (
        <div key={idx} className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            {id.type.replace(/_/g, " ")}
          </span>
          <div>
            <span className="font-mono">{id.value}</span>
            <ConfidenceBadgeComponent badge={id.badge} />
          </div>
        </div>
      ))}
    </div>
  );
}

function TablesSection({ tables }: { tables: ExtractedTable[] }) {
  if (tables.length === 0) {
    return (
      <p className="text-muted-foreground italic text-sm">No tables found</p>
    );
  }

  return (
    <div className="space-y-4">
      {tables.map((table) => (
        <div key={table.table_id} className="space-y-2">
          {table.title && (
            <p className="font-medium text-sm">{table.title}</p>
          )}
          <div className="border rounded-md overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {table.headers.map((header, idx) => (
                    <TableHead key={idx} className="text-xs">
                      {header}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {table.rows.map((row, rowIdx) => (
                  <TableRow key={rowIdx}>
                    {row.cells.map((cell, cellIdx) => (
                      <TableCell key={cellIdx} className="text-xs">
                        {cell}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      ))}
    </div>
  );
}

function SuccessPanel({ data }: { data: ExtractionResponse }) {
  const documentTypeLabels: Record<string, string> = {
    BOL: "Bill of Lading",
    COMMERCIAL_INVOICE: "Commercial Invoice",
    PACKING_LIST: "Packing List",
    UNKNOWN: "Unknown Document",
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Extracted Data
          <Badge variant="outline">
            {documentTypeLabels[data.document_type] || data.document_type}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 space-y-6 overflow-y-auto">
        {/* Canonical Fields */}
        <div>
          <h3 className="text-sm font-semibold mb-3">Document Fields</h3>
          <div className="divide-y">
            <FieldRow label="B/L Number" field={data.bill_of_lading_number} />
            <FieldRow label="Invoice Number" field={data.invoice_number} />
            <FieldRow label="Shipper" field={data.shipper_name} />
            <FieldRow label="Shipper Address" field={data.shipper_address} />
            <FieldRow label="Consignee" field={data.consignee_name} />
            <FieldRow label="Consignee Address" field={data.consignee_address} />
            <FieldRow label="Total Value" field={data.total_value_of_goods} />
          </div>
        </div>

        <Separator />

        {/* Identifiers */}
        <div>
          <h3 className="text-sm font-semibold mb-3">Other References Found</h3>
          <IdentifiersSection identifiers={data.identifiers} />
        </div>

        <Separator />

        {/* Tables */}
        <div>
          <h3 className="text-sm font-semibold mb-3">Extracted Tables</h3>
          <TablesSection tables={data.tables} />
        </div>
      </CardContent>
    </Card>
  );
}

export function ExtractionPanel({
  state,
  data,
  error,
  onRetry,
}: ExtractionPanelProps) {
  switch (state) {
    case "idle":
      return <IdlePanel />;
    case "processing":
      return <LoadingSkeleton />;
    case "error":
      return <ErrorPanel error={error || "Unknown error"} onRetry={onRetry} />;
    case "success":
      return data ? <SuccessPanel data={data} /> : <IdlePanel />;
    default:
      return <IdlePanel />;
  }
}
