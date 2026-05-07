"""
FastAPI application — DWR Reconciliation API.

Serves the static portfolio page and exposes POST /api/reconcile
for live PDF-to-reconciliation processing.
"""
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import run_pipeline

app = FastAPI(
    title="DWR Reconciliation API",
    description="AI-powered contract reconciliation for construction projects",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

ROOT_HTML = Path(__file__).parent.parent / "index.html"

MAX_PDF_BYTES = 5 * 1024 * 1024  # 5 MB per file


def _validate_pdf(data: bytes, field_name: str) -> None:
    if len(data) == 0:
        raise HTTPException(status_code=400, detail=f"{field_name}: file is empty")
    if len(data) > MAX_PDF_BYTES:
        mb = len(data) / 1_048_576
        raise HTTPException(
            status_code=413,
            detail=f"{field_name}: file too large ({mb:.1f} MB). Maximum is 5 MB."
        )
    # Verify PDF magic bytes (%PDF)
    if not data[:4] == b"%PDF":
        raise HTTPException(status_code=400, detail=f"{field_name}: not a valid PDF file")


@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(str(ROOT_HTML))


@app.post("/api/reconcile")
async def reconcile(
    ca_pdf: UploadFile = File(..., description="CA (Inspector) DWR PDF"),
    contractor_pdf: UploadFile = File(..., description="Contractor DWR PDF"),
):
    """
    Upload two DWR PDFs and receive a structured reconciliation report.
    Processing time: ~10–20 seconds (two concurrent Claude API calls).
    Maximum file size: 5 MB per PDF.
    """
    ca_bytes = await ca_pdf.read()
    con_bytes = await contractor_pdf.read()

    _validate_pdf(ca_bytes, "ca_pdf")
    _validate_pdf(con_bytes, "contractor_pdf")

    ca_tmp = None
    con_tmp = None
    try:
        ca_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        ca_tmp.write(ca_bytes)
        ca_tmp.flush()
        ca_tmp.close()

        con_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        con_tmp.write(con_bytes)
        con_tmp.flush()
        con_tmp.close()

        result = await run_pipeline(ca_tmp.name, con_tmp.name)
        return result

    except HTTPException:
        raise
    except Exception:
        # Do not expose internal error details to the caller
        raise HTTPException(status_code=500, detail="Processing failed. Please check your PDFs and try again.")
    finally:
        for tmp in (ca_tmp, con_tmp):
            if tmp is not None:
                try:
                    os.unlink(tmp.name)
                except (FileNotFoundError, AttributeError):
                    pass


@app.get("/health")
async def health():
    return {"status": "ok"}
