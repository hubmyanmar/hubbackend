import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def send_meeting_webhook_notification(
    meeting_title: str, 
    start_time: str, 
    meeting_room, 
    participants: list, 
    meeting_id: str
):
    webhook_url = os.getenv("ZOHO_CLIQ_WEBHOOK_URL")
    
    if not webhook_url:
        print("[Webhook Error] ZOHO_CLIQ_WEBHOOK_URL is not set or empty in .env")
        return

    room_name = ""
    if meeting_room:
        if hasattr(meeting_room, "name"):
            room_name = meeting_room.name
        elif hasattr(meeting_room, "title"):
            room_name = meeting_room.title
        elif isinstance(meeting_room, dict):
            room_name = meeting_room.get("name", meeting_room.get("title", ""))
        else:
            room_name = str(meeting_room)

    BASE_URL = os.getenv("FRONTEND_URL", "https://your-production-domain.com")
    mention_tags = []
    
    if isinstance(participants, list):
        for p in participants:
            email = None
            name = "User"

            if isinstance(p, dict):
                email = p.get("email")
                name = p.get("name", "User")
            elif isinstance(p, str):
                email = p
                name = p
            else:
                email = getattr(p, "email", None)
                name = getattr(p, "name", "User")

            if email and "@cliq.user" not in str(email):
                mention_tags.append(f"@{email}")
            elif name:
                mention_tags.append(f"@{name}")

    mentions_str = ", ".join(mention_tags) if mention_tags else "None"
    payload = {
        "text": (
            f"*Event Invite: {meeting_title}*\n\n"
            f"*When:* {start_time} (Asia/Rangoon)\n"
            f"*Where:* {room_name}\n"
            f"*Attendees:* {mentions_str}\n\n"
            f"[View Meeting]({BASE_URL}/meetings/{meeting_id})"
        )
    }

    print(f"[Webhook Debug] Sending request to Zoho Cliq Webhook...")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json=payload)
            
            print(f"[Webhook Response Status]: {response.status_code}")
            print(f"[Webhook Response Body]: {response.text}")

            if response.status_code != 200:
                print(f"[Webhook Failed] Status: {response.status_code}, Response: {response.text}")
            else:
                print("[Webhook Success] Notification sent successfully to Zoho Cliq!")

    except Exception as exc:
        print(f"[Webhook Exception]: {exc}")