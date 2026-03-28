from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.chat import router as chat_router
from app.routes.debug import router as debug_router
from app.routes.documents import router as docs_router
from app.schemas import HealthResponse
from app.services.rag import RagService

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(docs_router)
app.include_router(debug_router)


@app.on_event("startup")
async def startup_event():
    RagService().ingest_from_disk()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", app=settings.app_name)
