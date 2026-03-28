import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.deps import require_api_key
from app.schemas import ChatRequest, ChatResponse, IncidentAnalyzeRequest, IncidentAnalyzeResponse, SourceItem
from app.services.llm import LlmService
from app.services.logger import get_logger
from app.services.rag import RagService

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger("chat")
rag_service = RagService()
llm_service = LlmService()


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def chat(payload: ChatRequest):
    trace_id = str(uuid4())
    docs = rag_service.retrieve(payload.message, top_k=payload.top_k)
    context_blocks = [doc.page_content for doc in docs]
    llm_result = llm_service.generate(payload.message, context_blocks)
    sources = [
        SourceItem(source=doc.metadata.get("source", "unknown"), snippet=doc.page_content[:180])
        for doc in docs
    ]
    body = {
        "answer": llm_result["answer"],
        "sources": sources,
        "trace_id": trace_id,
        "debug": {
            "context_count": len(docs),
            "cache_hit": llm_result["cache"],
        },
    }
    logger.info(
        "chat_request_completed",
        extra={"extra_payload": {"trace_id": trace_id, "context_count": len(docs), "cache_hit": llm_result["cache"]}},
    )
    return body


@router.post("/chat/legacy", dependencies=[Depends(require_api_key)])
async def chat_legacy(payload: ChatRequest):
    trace_id = str(uuid4())
    docs = rag_service.retrieve(payload.message, top_k=payload.top_k)
    context_blocks = [doc.page_content for doc in docs]
    llm_result = llm_service.generate(payload.message, context_blocks)
    logger.error("legacy_response_format_detected", extra={"extra_payload": {"trace_id": trace_id}})
    return {
        "response": llm_result["answer"],
        "source_items": [
            {"source": doc.metadata.get("source", "unknown"), "snippet": doc.page_content[:180]}
            for doc in docs
        ],
        "request_id": trace_id,
        "meta": {"context_count": len(docs), "cache_hit": llm_result["cache"]},
    }


@router.post("/chat/stream", dependencies=[Depends(require_api_key)])
async def stream_chat(payload: ChatRequest):
    docs = rag_service.retrieve(payload.message, top_k=payload.top_k)
    context_blocks = [doc.page_content for doc in docs]
    trace_id = str(uuid4())

    async def event_generator():
        for token in llm_service.stream_tokens(payload.message, context_blocks):
            yield {"event": "token", "data": token}
            await asyncio.sleep(0)
        payload_done = json.dumps({"trace_id": trace_id, "sources": [doc.metadata.get("source", "unknown") for doc in docs]})
        yield {"event": "done", "data": payload_done}

    return EventSourceResponse(event_generator())


@router.post("/incident/analyze", response_model=IncidentAnalyzeResponse, dependencies=[Depends(require_api_key)])
async def analyze_incident(payload: IncidentAnalyzeRequest):
    trace_id = str(uuid4())
    docs = rag_service.retrieve(payload.incident, top_k=payload.top_k)
    context_blocks = [doc.page_content for doc in docs]
    result = llm_service.analyze_incident(payload.incident, context_blocks)
    sources = [
        SourceItem(source=doc.metadata.get("source", "unknown"), snippet=doc.page_content[:180])
        for doc in docs
    ]
    body = {
        "summary": result["summary"],
        "root_cause": result["root_cause"],
        "impact": result["impact"],
        "actions": result["actions"],
        "sources": sources,
        "trace_id": trace_id,
        "debug": {"context_count": len(docs)},
    }
    logger.info("incident_analysis_completed", extra={"extra_payload": {"trace_id": trace_id, "context_count": len(docs)}})
    return body
