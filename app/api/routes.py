from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.rag.workflow import ask
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file, chunk_documents, SUPPORTED
from app.services.audit import write_audit


router = APIRouter(prefix="/api")
settings = get_settings()


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
    }


@router.post("/chat")
def chat(payload: ChatRequest):
    try:
        result = ask(payload.question)

        write_audit(
            payload.question,
            result["source_used"],
            result.get("trace", []),
        )

        return {
            "answer": result["answer"],
            "source_used": result["source_used"],
            "trace": result.get("trace", []),
            "citations": result.get("citations", []),
            "rewritten_query": result.get(
                "current_query",
                payload.question,
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    x_admin_key: str = Header(default=""),
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin key",
        )

    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Supported: {', '.join(sorted(SUPPORTED))}",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    destination = upload_dir / Path(filename).name
    destination.write_bytes(await file.read())

    documents = load_file(destination)
    chunks = chunk_documents(documents)
    ids = add_documents(chunks)

    return {
        "message": "Document indexed",
        "file": destination.name,
        "chunks": len(chunks),
        "ids_created": len(ids),
    }