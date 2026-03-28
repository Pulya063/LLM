from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)


class SourceItem(BaseModel):
    source: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    trace_id: str
    debug: dict


class IncidentAnalyzeRequest(BaseModel):
    incident: str = Field(min_length=5, max_length=8000)
    top_k: int = Field(default=4, ge=1, le=10)


class IncidentAnalyzeResponse(BaseModel):
    summary: str
    root_cause: str
    impact: str
    actions: list[str]
    sources: list[SourceItem]
    trace_id: str
    debug: dict


class IngestRequest(BaseModel):
    file_name: str
    content: str


class IngestResponse(BaseModel):
    file_name: str
    chunks_added: int


class HealthResponse(BaseModel):
    status: str
    app: str
