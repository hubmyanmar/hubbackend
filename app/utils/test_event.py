import json
import requests

# OAuth Credentials
CLIENT_ID = "1000.ZL0P9GJWMHPVKQYT13KMG10MVAKCVH"
CLIENT_SECRET = "d0551dfaf1ef6887540b42ce06df39e8d88618e5ed"
REFRESH_TOKEN = "1000.fc640ddf367a2a81097713570ba7b53c.d18b2126b14ab068ecf1fd9bd8edfcc0"

# Channel Unique Chat ID (#meetingroombookingpilot)
CHANNEL_ID = "CT_1424471517690717894_867845712"


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


def process_meeting_booking():
    access_token = get_access_token()

    # -------------------------------------------------------------
    # STEP 1: Zoho Calendar API ဖြင့် Event ဖန်တီးပြီး Invite ပို့ခြင်း
    # -------------------------------------------------------------
    cal_url = "https://calendar.zoho.com/api/v1/calendars/primary/events"
    cal_headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    attendees_list = [
        "lilylucy2004@gmail.com",
        "nlo.businessdevelopment@gmail.com"
    ]

    event_dict = {
        "title": "BBC Meeting",
        "dateandtime": {
            "start": "20260925T140000",
            "end": "20260925T150000",
            "timezone": "Asia/Yangon"
        },
        "location": "Bagan Room",
        "description": "Meeting Room Booking Pilot Test",
        # Attendees ထံသို့ Invite Mail + Calendar Event အလိုအလျောက် ရောက်ရှိပါမည်
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

    # Event View Link ထုတ်ယူခြင်း
    events = cal_data.get("events", [])
    event_url = events[0].get("viewEventURL", "https://calendar.zoho.com") if events else "https://calendar.zoho.com"

   # -------------------------------------------------------------
    # STEP 2: Zoho Cliq Channel ထဲသို့ Notification Post တင်ခြင်း
    # -------------------------------------------------------------
    # CHAT_ID ကို သုံး၍ /chats/{CHAT_ID}/message သို့ ပို့ပေးရပါမည်
    cliq_url = f"https://cliq.zoho.com/api/v2/chats/{CHANNEL_ID}/message"
    
    cliq_headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    # Email များကို Cliq Profile Tag (<@email>) အဖြစ် ပြောင်းလဲခြင်း
    profile_mentions = ", ".join([f"<@{email}>" for email in attendees_list])

    cliq_payload = {
        "text": "📅 **New Meeting Scheduled: BBC Meeting**",
        "card": {
            "title": "BBC Meeting - Bagan Room",
            "theme": "modern-inline"
        },
        "slides": [
            {
                "type": "label",
                "data": [
                    {"Location": "Bagan Room"},
                    {"Time": "25 Sep 2026 (02:00 PM - 03:00 PM)"},
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

    return {
        "calendar_event": cal_data,
        "cliq_notification": cliq_data
    }


if __name__ == "__main__":
    try:
        result = process_meeting_booking()
        print("\nProcess finished successfully!")
    except Exception as e:
        print("\nExecution Error:", str(e))