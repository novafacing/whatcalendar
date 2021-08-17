from dataclasses import dataclass
from datetime import datetime


@dataclass
class Entry:
    """Represents a calendar or todo list entry"""
    todo: bool = False
    label: str = ""
    time: datetime = datetime.now()
