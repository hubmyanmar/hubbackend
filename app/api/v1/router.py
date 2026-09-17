from fastapi import APIRouter

from app.api.v1.endpoints import meeting_rooms, companies
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(meeting_rooms.router, prefix="/meeting-rooms", tags=["Meeting Rooms"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])