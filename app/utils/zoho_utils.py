# app/utils/zoho_utils.py
import os
import httpx

def send_meeting_webhook_notification(meeting_title: str, start_time: str, participants: list):
    webhook_url = os.getenv("ZOHO_CLIQ_WEBHOOK_URL")
    if not webhook_url:
        print("[Webhook Error] ZOHO_CLIQ_WEBHOOK_URL is not set in .env")
        return

    mention_tags = []
    for p in participants:
        email = p.get("email") if isinstance(p, dict) else getattr(p, "email", None)
        name = p.get("name", "User") if isinstance(p, dict) else getattr(p, "name", "User")
        
        if email and "@cliq.user" not in email:
            mention_tags.append(f"@{email}")
        else:
            mention_tags.append(f"@{name}")

    mentions_str = ", ".join(mention_tags)
    
    payload = {
        "text": f"📅 *New Meeting Booked!*\n\n"
                f"🔹 *Title:* {meeting_title}\n"
                f"⏰ *Time:* {start_time}\n"
                f"👥 *Invited Participants:* {mentions_str}\n\n"
                f"Please check your schedule and join on time!"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json=payload)
            if response.status_code != 200:
                print(f"[Webhook Failed] Status: {response.status_code}, Response: {response.text}")
    except Exception as exc:
        print(f"[Webhook Exception]: {exc}")
