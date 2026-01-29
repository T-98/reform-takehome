"use client";

import { useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PDFViewer } from "./pdf-viewer";
import { ExtractionPanel } from "./extraction-panel";
import { extractDocument } from "@/lib/api";
import { ExtractionResponse, UIState } from "@/lib/types";

export function DocumentPortal() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [extractionResult, setExtractionResult] = useState<ExtractionResponse | null>(null);
  const [uiState, setUiState] = useState<UIState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: extractDocument,
    onMutate: () => {
      setUiState("processing");
      setErrorMessage(null);
      setExtractionResult(null);
    },
    onSuccess: (data) => {
      setExtractionResult(data);
      setUiState("success");
    },
    onError: (error: Error) => {
      setErrorMessage(error.message);
      setUiState("error");
    },
  });

  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setErrorMessage("Please select a PDF file");
        setUiState("error");
        return;
      }

      setSelectedFile(file);
      setUiState("processing");
      mutation.mutate(file);
    },
    [mutation]
  );

  const handleRetry = useCallback(() => {
    if (selectedFile) {
      mutation.mutate(selectedFile);
    }
  }, [selectedFile, mutation]);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setExtractionResult(null);
    setUiState("idle");
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const isProcessing = uiState === "processing";

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Document Upload Portal</h1>
            <p className="text-muted-foreground">
              Upload a PDF to extract structured data
            </p>
          </div>
          {selectedFile && (
            <Button variant="outline" onClick={handleReset} disabled={isProcessing}>
              Upload New Document
            </Button>
          )}
        </div>

        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Upload PDF</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-center">
              <Input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileSelect}
                disabled={isProcessing}
                className="max-w-md"
              />
              {isProcessing && (
                <span className="text-sm text-muted-foreground">
                  Extracting data...
                </span>
              )}
              {selectedFile && !isProcessing && (
                <span className="text-sm text-muted-foreground">
                  {selectedFile.name}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Content - PDF Viewer + Extraction Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[540px] lg:h-[75vh] lg:max-h-[80vh]">
          {/* Left: PDF Viewer */}
          <div className="min-h-0">
            <PDFViewer file={selectedFile} />
          </div>

          {/* Right: Extraction Results */}
          <div className="min-h-0">
            <ExtractionPanel
              state={uiState}
              data={extractionResult}
              error={errorMessage}
              onRetry={handleRetry}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
