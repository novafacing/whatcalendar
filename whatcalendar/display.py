from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Tuple

from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont
from pytz import UTC 
from sortedcontainers import SortedDict

from whatcalendar.entry import Entry
from whatcalendar.modules import EntryModule

class DisplayManager:
    def __init__(
        self,
        config: Dict[str, Any],
        font_path: Path,
        interval: int,
        modules: List[EntryModule],
    ) -> None:
        """
        :param config: A dictionary of settings
        :param font_path: Path to the font file
        :param interval: How often to update the data (seconds)
        :param modules: A list of modules to use
        """
        self.font_size = 20  # Experimentally, this looks best.
        self.interval = interval
        self.config = config
        self.font = ImageFont.truetype(font_path.open("rb"), self.font_size)
        self.display = InkyWHAT("black")
        self.display.set_border(self.display.BLACK)
        self.img = Image.new("P", (self.display.WIDTH, self.display.HEIGHT))
        self.draw = ImageDraw.Draw(self.img)
        self.rows: List[Entry] = []
        self.modules: List[EntryModule] = list(map(lambda m: m(), modules))
        self.spacing = 2
        self.adjustment = 4
        self.per_page = (
            self.display.HEIGHT // self.font.getsize("ABCD ")[1] + self.spacing
        ) - self.adjustment

    def setup(self) -> None:
        """Run module setup methods"""
        for module in self.modules:
            module.setup(self.config)

    def assemble(self, sublist: List[Entry]) -> None:
        """
        Generate a string representation of the entries in a page.
        :param sublist: A list of entries for a page
        """
        assembled = ""
        for entry in sublist:
            initial = " "

            if (
                entry.time - datetime.now().replace(tzinfo=UTC)
            ).total_seconds() <= 3600:
                initial = "!"

            timestr = entry.time.strftime("%m/%d %H:%M")
            asmtxt = f"{initial}{timestr}|{entry.label}"
            if sum(map(lambda s: self.font.getsize(s)[0], asmtxt)) > self.display.WIDTH:
                while (
                    sum(map(lambda s: self.font.getsize(s)[0], asmtxt))
                    > self.display.WIDTH - self.font.getsize("-")[0]
                ):
                    asmtxt = asmtxt[:-1]
                asmtxt += "-"
            assembled += asmtxt + "\n"
        return assembled

    def show(self, sublist: List[Entry], page: Tuple[int]) -> None:
        """
        Display the page on screen
        :param sublist: The list of entries to in the page.
        """
        self.draw.multiline_text(
            (0, 0),
            self.assemble(sublist) + f"{' ' * 8}Page {page[0] + 1}/{page[1]} *** {datetime.now().replace(tzinfo=UTC).strftime('%H:%M')}",
            fill=self.display.BLACK,
            font=self.font,
            align="left",
            spacing=self.spacing,
        )
        self.display.set_image(self.img)
        self.display.show()

    def run(self) -> None:
        """Main loop, perform setup and start paginating."""
        self.setup()
        while True:
            events_list = self.refresh()
            pages = len(events_list) // self.per_page
            page_ranges = [
                (
                    i * self.per_page,
                    min((i * self.per_page) + self.per_page, len(events_list)),
                )
                for i in range(pages)
            ]

            for i, page_range in enumerate(page_ranges):
                self.show(events_list[page_range[0] : page_range[1]], (i, len(page_ranges)))
                self.draw.rectangle(
                    [0, 0, 400, 400], fill=self.display.WHITE, outline=None, width=0
                )
                sleep(self.config["settings"]["page-time"])

    def refresh(self) -> List[Entry]:
        """Refresh modules that need a refresh."""
        events = SortedDict()

        for module in self.modules:
            since_update = (datetime.now() - module.last).total_seconds()

            if since_update >= module.interval or module.data is None:
                module.refresh()

            for time, time_events in module.data.items():
                if time not in events:
                    events[time] = []
                events[time].extend(time_events)

        events_list = []

        for time in events:
            for event in events[time]:
                events_list.append(event)

        return events_list
