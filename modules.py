import abc
from dataclasses import dataclass
from datetime import datetime
from json import loads
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List, Optional

import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sortedcontainers import SortedDict

from entry import Entry


class EntryModule(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def refresh(self) -> List[Entry]:
        raise NotImplementedError

    @abc.abstractmethod
    def setup(self, config: Dict) -> None:
        raise NotImplementedError


@dataclass
class GoogleCalendarToken:
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: List[str]
    expiry: str


@dataclass
class GoogleCalendarProperties:
    token_identifier: str
    token: GoogleCalendarToken
    creds: Credentials
    token_file: Path
    flow: InstalledAppFlow
    calendar_ids: List[str]


@dataclass
class GoogleCalendarEvent:
    kind: Optional[Any] = None
    etag: Optional[Any] = None
    id: Optional[str] = None
    status: Optional[str] = None
    htmlLink: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    colorId: Optional[str] = None
    creator: Optional[Dict] = None
    organizer: Optional[Dict] = None
    start: Optional[Dict] = None
    end: Optional[Dict] = None
    endTimeUnspecified: Optional[bool] = None
    recurrence: Optional[List] = None
    recurringEventId: Optional[str] = None
    originalStartTime: Optional[Dict] = None
    transparency: Optional[str] = None
    visibility: Optional[str] = None
    iCalUID: Optional[str] = None
    sequence: Optional[Any] = None
    attendees: Optional[List] = None
    attendeesOmitted: Optional[bool] = None
    extendedProperties: Optional[Dict] = None
    hangoutLink: Optional[str] = None
    conferenceData: Optional[Dict] = None
    gadget: Optional[Dict] = None
    anyoneCanAddSelf: Optional[bool] = None
    guestsCanInviteOthers: Optional[bool] = None
    guestsCanModify: Optional[bool] = None
    guestsCanSeeOtherGuests: Optional[bool] = None
    privateCopy: Optional[bool] = None
    locked: Optional[bool] = None
    reminders: Optional[Dict] = None
    source: Optional[Dict] = None
    attachments: Optional[List] = None
    eventType: Optional[str] = None


class GoogleCalendarModule(EntryModule):
    def __init__(self) -> None:
        self.scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        self.interval = 180  # Once every other minute is more than enough
        self.last = datetime.now()
        self.data: Optional[SortedDict] = None

    def refresh(self) -> None:
        all_events = SortedDict()
        for credential in self.credentials:
            service = build("calendar", "v3", credentials=credential.creds)
            for calendar_id in credential.calendar_ids:
                now = datetime.utcnow().isoformat() + "Z"
                events_result = (
                    service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=now,
                        maxResults=16,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )

                events = events_result.get("items", [])

                for event in events:
                    gcal_event = GoogleCalendarEvent(**event)
                    event_time = datetime.fromisoformat(
                        gcal_event.start.get("dateTime", gcal_event.start.get("date"))
                    ).replace(tzinfo=pytz.UTC)
                    if event_time not in all_events:
                        all_events[event_time] = []
                    for item in self.blacklist:
                        if item in gcal_event.summary:
                            break
                    else:
                        all_events[event_time].append(
                            Entry(todo=False, label=gcal_event.summary, time=event_time)
                        )
        self.data = all_events

    def setup(self, config: Dict) -> None:
        self.credentials: List[GoogleCalendarProperties] = []
        if "calendar" not in config:
            raise AssertionError("No 'calendar' section in config!")

        tokens = config["calendar"]["tokens"]
        app_credentials_file = config["calendar"]["credentials"]
        ids = config["calendar"]["ids"]
        self.blacklist = config["calendar"]["blacklist"]

        for token_name, rel_tok_path in tokens.items():
            self.credentials.append(
                GoogleCalendarProperties(
                    token_identifier=token_name,
                    token=GoogleCalendarToken(
                        **loads((Path(__file__).parent / rel_tok_path).open("r").read())
                    ),
                    creds=Credentials.from_authorized_user_file(
                        Path(__file__).parent / rel_tok_path
                    ),
                    token_file=(Path(__file__).parent / rel_tok_path).resolve(),
                    flow=InstalledAppFlow.from_client_secrets_file(
                        Path(__file__).parent / app_credentials_file, self.scopes
                    ),
                    calendar_ids=ids[token_name],
                )
            )
