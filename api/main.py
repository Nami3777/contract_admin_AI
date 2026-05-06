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

# Serve static assets (CSS, images, etc.) if a static/ dir exists
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

ROOT_HTML = Path(__file__).parent.parent / "index.html"


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
    """
    if ca_pdf.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="ca_pdf must be a PDF file")
    if contractor_pdf.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="contractor_pdf must be a PDF file")

    ca_bytes = await ca_pdf.read()
    con_bytes = await contractor_pdf.read()

    if len(ca_bytes) == 0 or len(con_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded files must not be empty")

    ca_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    con_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        ca_tmp.write(ca_bytes)
        ca_tmp.flush()
        ca_tmp.close()

        con_tmp.write(con_bytes)
        con_tmp.flush()
        con_tmp.close()

        result = await run_pipeline(ca_tmp.name, con_tmp.name)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    finally:
        try:
            os.unlink(ca_tmp.name)
        except FileNotFoundError:
            pass
        try:
            os.unlink(con_tmp.name)
        except FileNotFoundError:
            pass


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY"))}
