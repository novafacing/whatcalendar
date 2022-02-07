import abc
from calendar import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, date, time
from json import loads
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List, Optional

import pytz
from pytz import timezone
from sortedcontainers import SortedDict
from gcsa import GoogleCalendar

from whatcalendar.entry import Entry


class EntryModule(metaclass=abc.ABCMeta):
    """Abstract class for modules that produce entries."""

    @abc.abstractmethod
    def refresh(self) -> List[Entry]:
        """Called when interval expires or to initialize the entry list."""
        raise NotImplementedError

    @abc.abstractmethod
    def setup(self, config: Dict) -> None:
        """Called before main loop to initialize module."""
        raise NotImplementedError


class SimpleGoogleCalendarModule(EntryModule):
    """Adds entries from a Google Calendar"""

    def __init__(self) -> None:
        """Initialize the calendar and update flags"""
        self.interval = 180  # Once every other minute is more than enough
        self.last = datetime.now()
        self.data: Optional[SortedDict] = None

    def refresh(self) -> None:
        """Refresh the calendar data."""
        all_events = SortedDict()
        for event in self.calendar.get_events(single_events=True):
            event_time = datetime.fromisoformat(event.start).replace(
                tzinfo=self.timezone
            )
            event_end_time = datetime.fromisoformat(event.end).replace(
                tzinfo=self.timezone
            )
            for item in self.denylist:
                if item in event.summary:
                    break
            else:
                now = datetime.now().replace(tzinfo=self.timezone)
                if event_time > now or (event_time <= now and event_end_time > now):
                    if event_time not in all_events:
                        all_events[event_time] = []
                    all_events[event_time].append(
                        Entry(todo=False, label=event.summary, time=event_time)
                    )

    def setup(self, config: Dict) -> None:
        """
        Set up identity and oauth.

        :param config: Configuration dictionary
        """
        self.config = config
        calendar_config = self.config.get("modules").get("calendar")
        self.timezone = timezone(self.config["settings"]["time-zone"])
        self.credentials_path = Path(__file__).parents[1] / calendar_config.get(
            "credentials"
        )
        self.token_path = self.credentials_path.parent / "token.pickle"
        self.denylist = calendar_config.get("denylist")
        self.calendar = GoogleCalendar(
            credentials_path=self.credentials_path, token_path=self.token_path
        )
