import json
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def get_youtube_service():
    creds = None
    if os.path.exists("outputs/token.json"):
        creds = Credentials.from_authorized_user_file("outputs/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("configs/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("outputs/token.json", "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def list_subscriptions():
    service = get_youtube_service()
    subs = []
    request = service.subscriptions().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50
    )
    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            subs.append({
                "channelId": item["snippet"]["resourceId"]["channelId"],
                "title": item["snippet"]["title"]
            })
        request = service.subscriptions().list_next(request, response)
    return subs

if __name__ == "__main__":
    subscriptions = list_subscriptions()
    print(f"Total subscriptions: {len(subscriptions)}")
    print(json.dumps(subscriptions[:1000], ensure_ascii=False, indent=2))
    with open("outputs/channels.json", "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=2)
