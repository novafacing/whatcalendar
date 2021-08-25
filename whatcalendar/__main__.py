import argparse
from json import loads
from pathlib import Path
from whatcalendar.display import DisplayManager
from whatcalendar.modules import GoogleCalendarModule

if __name__ == "__main__":
    parser = argparse.ArgumentParser("An extensible Pimoroni calendar application")
    parser.add_argument("--paginate", default=False, required=False, action="store_true", help="Whether to paginate (default: just show one page of events)")
    args = parser.add_args()
    config = loads((Path(__file__).parents[1] / "config" / "config.json").open("r").read())
    dm = DisplayManager(
        config=config, font_path=Path(__file__).parents[1] / config["settings"]["font-path"], interval=30, modules=[GoogleCalendarModule]
    )
    dm.run(paginate=args.paginate)