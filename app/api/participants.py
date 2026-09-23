from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import httpx

from app.db.session import get_db
from app.schemas import meeting_participant as mp_schemas
from app.crud import meeting_participant as mp_crud

# Attempt to reuse Zoho auth helper from existing auth endpoint
try:
    from app.api.v1.endpoints.auth import get_zoho_access_token, ZOHO_CLIQ_USER_URL
except Exception:
    get_zoho_access_token = None
    ZOHO_CLIQ_USER_URL = "https://cliq.zoho.com/api/v2/users"

router = APIRouter(prefix="/participants", tags=["participants"])


@router.get("/meetings/{meeting_id}", response_model=List[mp_schemas.MeetingParticipantOut])
def list_participants(meeting_id: int, db: Session = Depends(get_db)):
    return mp_crud.list_participants_by_meeting(db=db, meeting_id=meeting_id)


@router.post("/", response_model=mp_schemas.MeetingParticipantOut, status_code=status.HTTP_201_CREATED)
def create_participant(payload: mp_schemas.MeetingParticipantCreate, db: Session = Depends(get_db)):
    # Basic check: meeting must exist
    meeting = db.execute("SELECT 1 FROM meetings WHERE id = :id", {"id": payload.meeting_id}).first()
    if not meeting:
        raise HTTPException(status_code=400, detail="meeting_id not found")
    return mp_crud.create_participant(db=db, payload=payload)


@router.post("/sync-zoho/{meeting_id}", response_model=List[mp_schemas.MeetingParticipantOut])
def sync_from_zoho(meeting_id: int, db: Session = Depends(get_db)):
    if get_zoho_access_token is None:
        raise HTTPException(status_code=500, detail="Zoho helper not available")

    # Ensure meeting exists
    meeting = db.execute("SELECT 1 FROM meetings WHERE id = :id", {"id": meeting_id}).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Fetch users from Zoho (simple pagination)
    token = get_zoho_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    users_accum = []
    limit = 100
    next_token = None
    url = ZOHO_CLIQ_USER_URL

    while True:
        req_url = f"{url}?limit={limit}"
        if next_token:
            req_url += f"&next_token={next_token}"

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(req_url, headers=headers)
            if resp.status_code != 200:
                break
            payload = resp.json()

        users_list = []
        if isinstance(payload, dict):
            users_list = payload.get("users") or payload.get("data") or []
        elif isinstance(payload, list):
            users_list = payload

        if not users_list:
            break

        for u in users_list:
            if not isinstance(u, dict):
                continue

            # Extract zoho user id
            zoho_id = u.get("id") or u.get("user_id") or u.get("zoho_user_id") or u.get("userid")

            # Extract email
            email = u.get("email") or u.get("email_id") or u.get("primary_email")

            # Extract name — try display name or first/last
            name = u.get("display_name") or u.get("displayName") or u.get("name")
            if not name:
                first = u.get("first_name") or u.get("firstName") or ""
                last = u.get("last_name") or u.get("lastName") or ""
                name = f"{first} {last}".strip()

            if not zoho_id or not email:
                continue

            # Clean name and optionally extract position using a helper
            try:
                from app.utils.zoho_sync import split_name_and_position
                clean_name, _position = split_name_and_position(name)
            except Exception:
                # Fallback: simple split on ' - '
                if isinstance(name, str) and " - " in name:
                    clean_name = name.split(" - ", 1)[0].strip()
                else:
                    clean_name = name or ""

            users_accum.append({
                "zoho_user_id": str(zoho_id),
                "email": str(email).strip(),
                "name": str(clean_name).strip() if clean_name else "",
            })

        # pagination
        pagination = payload.get("pagination", {}) if isinstance(payload, dict) else {}
        next_token = payload.get("next_token") or pagination.get("next_token") or payload.get("next_set_token")
        if not next_token or len(users_list) < limit:
            break

    # Upsert into DB
    results = mp_crud.bulk_sync_from_zoho(db=db, meeting_id=meeting_id, users=users_accum)
    return results


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(participant_id: int, db: Session = Depends(get_db)):
    obj = mp_crud.get_participant(db=db, participant_id=participant_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Participant not found")
    mp_crud.delete_participant(db=db, participant=obj)
    return None
