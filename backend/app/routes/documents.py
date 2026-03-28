from pathlib import Path

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import require_api_key
from app.schemas import IngestRequest, IngestResponse
from app.services.logger import get_logger
from app.services.rag import RagService

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = get_logger("documents")
rag_service = RagService()


@router.get("", dependencies=[Depends(require_api_key)])
async def list_documents():
    docs = [p.name for p in Path(settings.docs_dir).glob("*.txt")]
    return {"documents": docs}


@router.post("/ingest", response_model=IngestResponse, dependencies=[Depends(require_api_key)])
async def ingest_document(payload: IngestRequest):
    file_path = Path(settings.docs_dir) / payload.file_name
    file_path.write_text(payload.content, encoding="utf-8")
    chunks = rag_service.ingest_text(payload.content, str(file_path))
    logger.info("document_ingested", extra={"extra_payload": {"file": payload.file_name, "chunks": chunks}})
    return IngestResponse(file_name=payload.file_name, chunks_added=chunks)
