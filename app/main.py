import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api.v1.router import api_router

app = FastAPI(title="Minutemind Backend")

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_CRM_LEADS_URL = "https://www.zohoapis.com/crm/v2/Leads"


def get_zoho_credentials(require_refresh_token: bool = True) -> tuple[str, str, Optional[str]]:
    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")
    refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Zoho credentials are missing. Set ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET in .env file."
        )

    if require_refresh_token and not refresh_token:
        raise RuntimeError(
            "ZOHO_REFRESH_TOKEN is missing in .env file."
        )

    return client_id, client_secret, refresh_token


def get_zoho_access_token() -> str:
    client_id, client_secret, refresh_token = get_zoho_credentials(require_refresh_token=True)
    payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(ZOHO_TOKEN_URL, data=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Zoho token request failed with status {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Zoho token refresh response did not include an access_token: {data}")
    return token


@app.get("/api/zoho/crm-leads")
def zoho_crm_leads(
    limit: int = Query(200, ge=1, le=200),
    page: int = Query(1, ge=1),
):
    try:
        token = get_zoho_access_token()
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}
        params = {"page": page, "per_page": limit}

        with httpx.Client(timeout=30.0) as client:
            response = client.get(ZOHO_CRM_LEADS_URL, headers=headers, params=params)

        if response.status_code != 200:
            return {
                "data": [],
                "count": 0,
                "error": f"Zoho CRM request failed with status {response.status_code}: {response.text[:500]}",
            }

        payload = response.json()
        data = payload.get("data") or []
        info = payload.get("info") or {}
        return {"data": data, "count": len(data), "info": info}
    except Exception as exc:
        return {"data": [], "count": 0, "error": str(exc)}


@app.get("/api/zoho/callback")
async def zoho_callback(code: Optional[str] = None):
    if not code:
        return {
            "status": "error",
            "message": "code parameter ပါမလာပါ။ Zoho Authorization URL မှတစ်ဆင့် ဝင်ရောက်ပါ။",
        }

    try:
        client_id, client_secret, _ = get_zoho_credentials(require_refresh_token=False)
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc)}

    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "http://localhost:8000/api/zoho/callback",
        "code": code,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ZOHO_TOKEN_URL, data=payload)
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Zoho authorization failed with status {response.status_code}: {response.text[:500]}",
            }
        tokens = response.json()
        return {"status": "success", "tokens": tokens}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}