import requests

# Access Token ပြန်ယူသည့် Function
def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        "refresh_token": "1000.b0d9d7d880f2f150b803a89fb36ebeb8.120af0faab3e4e44d2ff602b7c129470",
        "client_id": "1000.ZL0P9GJWMHPVKQYT13KMG10MVAKCVH",
        "client_secret": "d0551dfaf1ef6887540b42ce06df39e8d88618e5ed",
        "grant_type": "refresh_token"
    }
    res = requests.post(url, data=payload)
    return res.json().get("access_token")

# Calendar List အကုန်ဆွဲထုတ်ခြင်း
access_token = get_access_token()
url = "https://calendar.zoho.com/api/v1/calendars"
headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

response = requests.get(url, headers=headers)
calendars = response.json().get("calendars", [])

for cal in calendars:
    print(f"Name: {cal.get('name')} | Calendar ID (uid): {cal.get('uid')}")