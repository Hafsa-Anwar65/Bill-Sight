"""FastAPI app: JSON API under /api, and the built React app at /."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import llm, service
from .analysis import answer_all
from .config import settings
from .export import level1_csv, level2_csv
from .schema import Bill

MAX_UPLOAD = 15 * 1024 * 1024
IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

app = FastAPI(title="Billsight", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    bill: Bill
    question: str = Field(min_length=1, max_length=500)


class ExportItem(BaseModel):
    bill_id: str
    bill: Bill | None = None


class ExportRequest(BaseModel):
    items: list[ExportItem]


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "model": llm.model_name(), "api_key_set": bool(settings.api_key)}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), use_cache: bool = True) -> dict:
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(415, "Upload a PNG, JPG or WEBP image of the bill.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "The file is empty.")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "The image is larger than 15 MB.")
    bill_id = Path(file.filename or "bill").stem
    try:
        return service.analyze(data, bill_id, use_cache=use_cache)
    except llm.LLMError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.post("/api/ask")
def ask(req: AskRequest) -> dict:
    try:
        return {"answer": service.ask(req.bill, req.question)}
    except llm.LLMError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.post("/api/export")
def export(req: ExportRequest) -> dict:
    l1 = [(i.bill_id, i.bill) for i in req.items]
    l2 = [(i.bill_id, answer_all(i.bill)) for i in req.items if i.bill]
    return {"level1_csv": level1_csv(l1), "level2_csv": level2_csv(l2)}


# Serve the built frontend (npm run build) from the same server.
dist = settings.frontend_dist
if dist.exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        target = dist / path
        return FileResponse(target if path and target.is_file() else dist / "index.html")
