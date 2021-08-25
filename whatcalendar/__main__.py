from json import loads
from pathlib import Path
from whatcalendar.display import DisplayManager
from whatcalendar.modules import GoogleCalendarModule

if __name__ == "__main__":
    config = loads((Path(__file__).parents[1] / "config" / "config.json").open("r").read())
    dm = DisplayManager(
        config=config, font_path=Path(__file__).parents[1] / config["settings"]["font-path"], interval=30, modules=[GoogleCalendarModule]
    )
    dm.run(paginate=config["settings"]["paginate"])