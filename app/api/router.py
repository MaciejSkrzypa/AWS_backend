from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.media import router as media_router
from app.api.messages import router as messages_router
from app.api.rooms import router as rooms_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(rooms_router)
api_router.include_router(messages_router)
api_router.include_router(media_router)
