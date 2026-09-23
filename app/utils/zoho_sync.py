from datetime import datetime
import json
import os
import requests

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")


def get_access_token():
    """Zoho OAuth Server မှ Access Token တောင်းယူခြင်း"""
    url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(url, data=payload)
    token_data = response.json()
    
    if "access_token" in token_data:
        return token_data["access_token"]
    else:
        raise Exception(f"OAuth Token Error: {token_data}")


def send_zoho_notification(meeting_title, start_time, end_time, participants, meeting_room, meeting_id):
    """Meeting Booking လုပ်လိုက်သည်နှင့် Zoho Calendar နှင့် Cliq သို့ ပို့ပေးသော Function"""
    try:
        access_token = get_access_token()

        cal_url = "https://calendar.zoho.com/api/v1/calendars/primary/events"
        cal_headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        attendees_list = []
        for p in participants:
            email = p.get("email") if isinstance(p, dict) else getattr(p, "email", None)
            if email:
                attendees_list.append(email)
        room_name = getattr(meeting_room, "name", str(meeting_room)) if meeting_room else "Bagan Room"

        start_str_full = str(start_time)
        date_display_str = "2026-09-25"
        
        if " " in start_str_full:
            m_date_part, time_part = start_str_full.split(" ", 1)
            m_date_str = m_date_part.replace("-", "")
            start_formatted = f"{m_date_str}T{time_part.replace(':', '')[:6]}"
            date_display_str = m_date_part
        else:
            m_date_str = date_display_str.replace("-", "")
            start_formatted = f"{m_date_str}T{start_str_full.replace(':', '')[:6]}"

        end_str_full = str(end_time)
        if " " in end_str_full:
            _, end_time_part = end_str_full.split(" ", 1)
            end_formatted = f"{m_date_str}T{end_time_part.replace(':', '')[:6]}"
        else:
            end_formatted = f"{m_date_str}T{end_str_full.replace(':', '')[:6]}"

        event_dict = {
            "title": meeting_title,
            "dateandtime": {
                "start": start_formatted,
                "end": end_formatted,
                "timezone": "Asia/Yangon"
            },
            "location": room_name,
            "description": f"Meeting Room Booking Pilot Test (ID: {meeting_id})",
            "attendees": [{"email": email} for email in attendees_list]
        }

        print("Step 1: Creating Calendar Event & Sending Invites...")
        cal_response = requests.post(
            cal_url, 
            headers=cal_headers, 
            data={"eventdata": json.dumps(event_dict)}
        )
        cal_data = cal_response.json()
        print("Calendar API Response:", json.dumps(cal_data, indent=2))

        events = cal_data.get("events", [])
        event_url = events[0].get("viewEventURL", "https://calendar.zoho.com") if events else "https://calendar.zoho.com"

        cliq_url = f"https://cliq.zoho.com/api/v2/chats/{CHANNEL_ID}/message"
        
        cliq_headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        profile_mentions = ", ".join([f"<@{email}>" for email in attendees_list]) if attendees_list else "None"
        def format_to_ampm(t_obj):
            if not t_obj:
                return ""
            t_str = str(t_obj).strip()
            try:
                dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%I:%M %p")
            except ValueError:
                pass
            try:
                dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M")
                return dt.strftime("%I:%M %p")
            except ValueError:
                pass
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    dt = datetime.strptime(t_str, fmt)
                    return dt.strftime("%I:%M %p")
                except ValueError:
                    pass

            return t_str

        formatted_start = format_to_ampm(start_time)
        formatted_end = format_to_ampm(end_time)
        time_display_str = f"{formatted_start} - {formatted_end}"

        cliq_payload = {
            "text": f"📅 **New Meeting Scheduled: {meeting_title}**",
            "card": {
                "title": f"{meeting_title} - {room_name}",
                "theme": "modern-inline"
            },
            "slides": [
                {
                    "type": "label",
                    "data": [
                        {"Location": room_name},
                        {"Time": time_display_str},
                        {"Attendees": profile_mentions}
                    ]
                },
                {
                    "type": "text",
                    "data": f"🔗 [Open in Zoho Calendar]({event_url})"
                }
            ]
        }

        print(f"\nStep 2: Posting Notification Card to Channel Chat (ID: {CHANNEL_ID})...")
        cliq_response = requests.post(cliq_url, headers=cliq_headers, json=cliq_payload)
        
        try:
            cliq_data = cliq_response.json()
        except Exception:
            cliq_data = {
                "http_status": cliq_response.status_code,
                "raw_response": cliq_response.text
            }
            
        print("Cliq API Response:", json.dumps(cliq_data, indent=2))

    except Exception as e:
        print("Zoho API Sync Background Error:", str(e))