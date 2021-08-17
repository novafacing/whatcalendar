from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

creds = None
token_file = Path(__file__).parent / "config" / "personal_token.json"
if token_file.exists():
    creds = Credentials.from_authorized_user_file("config/personal_token.json")

if creds is None or not creds.valid:
    if creds is not None and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "config/personal_credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with token_file.open("w") as token:
        token.write(creds.to_json())

service = build("calendar", "v3", credentials=creds)

now = datetime.utcnow().isoformat() + "Z"
events_result = (
    service.events()
    .list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    )
    .execute()
)

events = events_result.get("items", [])

if not events:
    print("No upcoming events.")

for event in events:
    print("EVENT: ", event)
    start = event["start"].get("dateTime", event["start"].get("date"))
    print(start, event["summary"])
