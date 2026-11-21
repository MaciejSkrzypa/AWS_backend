from fastapi import APIRouter, Depends

from app.auth import require_cognito_access_token
from app.api.health import router as health_router
from app.api.media import router as media_router
from app.api.messages import router as messages_router
from app.api.rooms import router as rooms_router

api_router = APIRouter(prefix="/api")
authenticated_router = APIRouter(dependencies=[Depends(require_cognito_access_token)])

api_router.include_router(health_router)
authenticated_router.include_router(rooms_router)
authenticated_router.include_router(messages_router)
authenticated_router.include_router(media_router)
api_router.include_router(authenticated_router)
