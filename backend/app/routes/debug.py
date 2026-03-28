from pathlib import Path

from fastapi import APIRouter, Depends

from app.deps import require_api_key

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/logs", dependencies=[Depends(require_api_key)])
async def read_logs(limit: int = 50):
    log_file = Path("./backend.log")
    if not log_file.exists():
        return {"logs": []}
    lines = log_file.read_text(encoding="utf-8").splitlines()
    return {"logs": lines[-limit:]}
