"use client";

import { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

// Import react-pdf styles (required for TextLayer and AnnotationLayer)
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

// Dynamically import react-pdf components to avoid SSR issues
const Document = dynamic(
  () => import("react-pdf").then((mod) => mod.Document),
  { ssr: false }
);
const Page = dynamic(() => import("react-pdf").then((mod) => mod.Page), {
  ssr: false,
});

interface PDFViewerProps {
  file: File | null;
}

export function PDFViewer({ file }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [pdfReady, setPdfReady] = useState(false);

  // Configure PDF.js worker on mount
  useEffect(() => {
    import("react-pdf").then((pdfjs) => {
      pdfjs.pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.pdfjs.version}/build/pdf.worker.min.mjs`;
      setPdfReady(true);
    });
  }, []);

  const onDocumentLoadSuccess = useCallback(
    ({ numPages }: { numPages: number }) => {
      setNumPages(numPages);
      setPageNumber(1);
      setError(null);
    },
    []
  );

  const onDocumentLoadError = useCallback((err: Error) => {
    setError(err.message);
  }, []);

  if (!file) {
    return (
      <Card className="h-full flex items-center justify-center bg-muted/50">
        <CardContent className="text-center text-muted-foreground">
          <p>Upload a PDF to preview</p>
        </CardContent>
      </Card>
    );
  }

  if (!pdfReady) {
    return (
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 p-4">
          <Skeleton className="h-full w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardContent className="flex-1 overflow-y-auto p-4">
        {error ? (
          <div className="flex items-center justify-center h-full text-destructive">
            Failed to load PDF: {error}
          </div>
        ) : (
          <Document
            file={file}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Loading PDF...
              </div>
            }
            className="flex justify-center"
          >
            <Page
              pageNumber={pageNumber}
              loading={
                <div className="flex items-center justify-center h-64 text-muted-foreground">
                  Loading page...
                </div>
              }
              width={500}
            />
          </Document>
        )}
      </CardContent>

      {numPages && numPages > 1 && (
        <div className="flex items-center justify-center gap-4 p-3 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {pageNumber} of {numPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
            disabled={pageNumber >= numPages}
          >
            Next
          </Button>
        </div>
      )}
    </Card>
  );
}
