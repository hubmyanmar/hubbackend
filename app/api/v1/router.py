from fastapi import APIRouter

# app/api/meetings.py ထဲမှ တိုက်ရိုက် import လုပ်ခြင်း
from app.api import meetings
from app.api import meeting_records, action_items
from app.api.v1.endpoints import meeting_rooms, companies, meeting_sessions, uploads, translate
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(meeting_rooms.router, prefix="/meeting-rooms", tags=["Meeting Rooms"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])

api_router.include_router(meetings.router)
api_router.include_router(meeting_records.router)
api_router.include_router(action_items.router)
api_router.include_router(meeting_sessions.router)
api_router.include_router(uploads.lookup_router)
api_router.include_router(uploads.router)
api_router.include_router(translate.router)
