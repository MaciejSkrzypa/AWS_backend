import asyncio

from fastapi import APIRouter, Query

router = APIRouter(prefix="/demo", tags=["monitoring"])


@router.get("/slow")
async def simulate_slow_response(
    delay_ms: int = Query(default=2500, ge=0, le=10000),
) -> dict[str, int]:
    await asyncio.sleep(delay_ms / 1000)
    return {"delay_ms": delay_ms}
