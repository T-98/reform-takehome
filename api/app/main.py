"""FastAPI backend for document extraction."""
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .schemas import ExtractionResponse
from .extraction import ExtractionService

load_dotenv()

app = FastAPI(
    title="Document Extraction API",
    description="Extract structured data from scanned PDFs using OpenAI vision",
    version="1.0.0"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extraction_service = ExtractionService()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/documents", response_model=ExtractionResponse)
async def extract_document(file: UploadFile = File(...)):
    """
    Extract structured data from a PDF document.

    - Accepts multipart/form-data with a PDF file
    - Returns extracted fields, identifiers, tables, and confidence scores
    - Synchronous: waits for extraction to complete
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=422, detail="No filename provided")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are supported")

    if file.content_type and file.content_type != "application/pdf":
        # Be lenient - some browsers send different content types
        pass

    # Read file contents
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(contents) == 0:
        raise HTTPException(status_code=422, detail="Empty file")

    # Max file size: 10MB
    max_size = 10 * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(status_code=422, detail="File too large (max 10MB)")

    # Extract
    try:
        result = extraction_service.extract_from_pdf(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    # If extraction had an error, return 500
    if result.extraction_error:
        raise HTTPException(status_code=500, detail=result.extraction_error)

    return result
