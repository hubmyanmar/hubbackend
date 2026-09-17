# app package
from fastapi import FastAPI

app = FastAPI(title="MinuteMind Backend")

# include routers lazily to avoid import side-effects
try:
    from app.api import meetings as meetings_router
    app.include_router(meetings_router.router)
except Exception:
    # If imports fail (e.g., during initial scaffold), ignore — developer can import later
    pass

try:
    from app.api import meeting_records as meeting_records_router
    app.include_router(meeting_records_router.router)
except Exception:
    # Ignore if import fails during scaffold
    pass

try:
    from app.api import action_items as action_items_router
    app.include_router(action_items_router.router)
except Exception:
    # Ignore if import fails during scaffold
    pass
