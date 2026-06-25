"""
FastAPI application — DWR Reconciliation API.

Serves the static portfolio page and exposes POST /api/reconcile
for live PDF-to-reconciliation processing.
"""
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

ROOT_HTML = Path(__file__).parent.parent / "frontend" / "index.html"

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

    with tempfile.TemporaryDirectory() as tmpdir:
        ca_path = Path(tmpdir) / "ca.pdf"
        con_path = Path(tmpdir) / "con.pdf"
        ca_path.write_bytes(ca_bytes)
        con_path.write_bytes(con_bytes)
        try:
            return await run_pipeline(str(ca_path), str(con_path))
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Processing failed. Please check your PDFs and try again.")


@app.get("/health")
async def health():
    return {"status": "ok"}
