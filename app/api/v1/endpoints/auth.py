import os
import time
import re
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.crud import crud_user
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserCreate, UserOut
from app.core.security import get_current_user

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_CLIQ_USER_URLS = [
    "https://cliq.zoho.com/api/v2/users",
]

CACHE_TTL_SECONDS = 3600  # 1 hour
_positions_cache = {
    "data": [],
    "last_fetched": 0.0
}

def get_zoho_access_token() -> str:
    refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")

    if not all([refresh_token, client_id, client_secret]):
        print("[Zoho Error] Missing environment variables in .env")
        raise RuntimeError("Missing Zoho env values in .env")

    payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(ZOHO_TOKEN_URL, data=payload)
        response.raise_for_status()
        data = response.json()

    token = data.get("access_token")
    if not token:
        print(f"[Zoho Error] Token Response failed: {data}")
        raise RuntimeError(f"Zoho token request failed: {data}")
    
    return token
def get_company_positions_from_zoho() -> list[str]:
    try:
        token = get_zoho_access_token()
    except Exception as exc:
        print(f"[Zoho Auth Error]: {exc}")
        return []

    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    seen_lower: set[str] = set()
    positions: list[str] = []

    url = "https://cliq.zoho.com/api/v2/users"
    limit = 100
    next_token = None

    while True:
       
        req_url = f"{url}?limit={limit}"
        if next_token:
            req_url += f"&next_token={next_token}"
            
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(req_url, headers=headers)

            if response.status_code != 200:
                print(f"[Zoho API Break/Error] URL: {req_url} - Status: {response.status_code}")
                
                break

            payload = response.json()
            users_list = []
            if isinstance(payload, dict):
                users_list = payload.get("users") or payload.get("data") or []
            elif isinstance(payload, list):
                users_list = payload

            print(f"[DEBUG] Received {len(users_list)} users in this batch. (Token: {next_token})")
            if not users_list:
                break

            for user in users_list:
                if not isinstance(user, dict):
                    continue

                extracted_pos = None

                for key in ("designation", "title", "job_title", "jobTitle", "position"):
                    val = user.get(key)
                    if val and isinstance(val, str) and val.strip():
                        extracted_pos = val.strip()
                        break

                if not extracted_pos:
                    first_name = user.get("first_name") or ""
                    last_name = user.get("last_name") or ""
                    full_name_field = f"{first_name} {last_name}".strip()
                    
                    possible_text_sources = [
                        user.get("display_name"),
                        user.get("displayName"),
                        user.get("name"),
                        full_name_field,
                    ]

                    for raw_val in possible_text_sources:
                        if not raw_val or not isinstance(raw_val, str):
                            continue
                        
                        val_clean = raw_val.strip()
                        parts = re.split(r'\s*[-–—|/]\s*', val_clean)
                        if len(parts) >= 2:
                            extracted_pos = parts[-1].strip()
                            break

                if extracted_pos and len(extracted_pos) > 1:
                    clean_pos = " ".join(extracted_pos.split())
                    normalized_pos = clean_pos.lower()

                    if normalized_pos not in seen_lower:
                        seen_lower.add(normalized_pos)
                        positions.append(clean_pos)

            pagination = payload.get("pagination", {})
            next_token = payload.get("next_token") or pagination.get("next_token") or payload.get("next_set_token")
            
            if not next_token or len(users_list) < limit:
                break

        except Exception as exc:
            print(f"[Zoho Extraction Loop Error]: {exc}")
            break

    print(f"[DEBUG] Total Unique Positions Extracted: {len(positions)}")
    return positions

def get_allowed_positions() -> list[str]:
    global _positions_cache
    current_time = time.time()

    if current_time - _positions_cache["last_fetched"] < CACHE_TTL_SECONDS and _positions_cache["data"]:
        return _positions_cache["data"]

    company_positions = get_company_positions_from_zoho()
    sorted_positions = sorted(set(company_positions))

    if sorted_positions:
        _positions_cache["data"] = sorted_positions
        _positions_cache["last_fetched"] = current_time

    return _positions_cache["data"]


@router.get("/positions")
def get_positions():
    return {"positions": get_allowed_positions()}

# Caching အတွက် 
_users_cache = {
    "data": [],
    "last_fetched": 0.0
}
def get_company_users_from_zoho() -> list[dict]:
    try:
        token = get_zoho_access_token()
    except Exception as exc:
        print(f"[Zoho Auth Error]: {exc}")
        return []

    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    users_result = []
    seen_emails = set()

    url = "https://cliq.zoho.com/api/v2/users"
    limit = 100
    next_token = None

    while True:
        req_url = f"{url}?limit={limit}"
        if next_token:
            req_url += f"&next_token={next_token}"
            
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(req_url, headers=headers)

            if response.status_code != 200:
                print(f"[Zoho API Error] URL: {req_url} - Status: {response.status_code}")
                break

            payload = response.json()
            users_list = []
            if isinstance(payload, dict):
                users_list = payload.get("users") or payload.get("data") or []
            elif isinstance(payload, list):
                users_list = payload

            if not users_list:
                break

            for user in users_list:
                if not isinstance(user, dict):
                    continue

                display_name = (
                    user.get("display_name") or 
                    user.get("displayName") or 
                    user.get("name") or 
                    f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                )

                email = (
                    user.get("email") or 
                    user.get("email_id") or 
                    user.get("mail") or 
                    user.get("user_email")
                )

                zoho_user_id = user.get("id") or user.get("zuid") or user.get("user_id")

                if display_name:
                    clean_email = (
                        email.strip().lower() 
                        if email and isinstance(email, str) 
                        else f"{str(zoho_user_id or display_name).lower().replace(' ', '_')}@cliq.user"
                    )
                    
                    if clean_email not in seen_emails:
                        seen_emails.add(clean_email)
                        users_result.append({
                            "zoho_user_id": str(zoho_user_id) if zoho_user_id else "",
                            "name": str(display_name).strip(),
                            "email": clean_email
                        })

            pagination = payload.get("pagination", {})
            next_token = payload.get("next_token") or pagination.get("next_token") or payload.get("next_set_token")
            
            if not next_token or len(users_list) < limit:
                break

        except Exception as exc:
            print(f"[Zoho Users Extraction Loop Error]: {exc}")
            break

    print(f"[DEBUG] Total Unique Users Extracted: {len(users_result)}")
    return users_result

def get_allowed_users() -> list[dict]:
    global _users_cache
    current_time = time.time()

    if current_time - _users_cache["last_fetched"] < CACHE_TTL_SECONDS and _users_cache["data"]:
        return _users_cache["data"]

    company_users = get_company_users_from_zoho()
    if company_users:
        _users_cache["data"] = company_users
        _users_cache["last_fetched"] = current_time

    return _users_cache["data"]

@router.get("/users")
def get_zoho_users_list():
    return get_allowed_users()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    if crud_user.get_user_by_email(db, str(payload.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user_payload = UserCreate(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        position=payload.position,
        image=payload.image,
    )
    return crud_user.create_user(db, user_payload)


@router.post("/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, str(payload.email))
    if not user or not user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not crud_user.verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "position": user.position,
    })

    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "position": user.position,
            "image": user.image
        }
    }

@router.patch("/update-image")
def update_profile_image(
    payload: dict, 
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    image_data = payload.get("image")
    
    current_user.image = image_data
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Image updated successfully", "image": current_user.image}