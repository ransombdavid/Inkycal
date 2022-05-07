#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Calendar module for Inky-Calendar Project
Copyright by aceisace
"""
from inkycal.modules.modules_utilities.gcalendar_utils import get_events, filter_events
from inkycal.modules.template import inkycal_module
from inkycal.custom import *

import calendar as cal
import arrow

filename = os.path.basename(__file__).split(".py")[0]
logger = logging.getLogger(filename)


class GoogleCalendar(inkycal_module):
    """GoogleCalendar class
    Create monthly calendar and show events from given google calendar
    """

    name = "Calendar - Show monthly calendar with events from Google Calendar"

    required = {
        "calendar_ids": {
            "label": "Google email address, shared with a service account",
        },
        "credentials_file": {"label": "Service account credentials file (JSON)"},
    }

    optional = {
        "week_starts_on": {
            "label": "When does your week start? (default=Monday)",
            "options": ["Monday", "Sunday"],
            "default": "Monday",
        },
        "show_events": {
            "label": "Show parsed events? (default = True)",
            "options": [True, False],
            "default": True,
        },
        "date_format": {
            "label": "Use an arrow-supported token for custom date formatting "
            + "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. D MMM",
            "default": "D MMM",
        },
        "time_format": {
            "label": "Use an arrow-supported token for custom time formatting "
            + "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. HH:mm",
            "default": "HH:mm",
        },
        "language": {
            "label": "Language abbreviation, i.e. 'en', 'fr', 'rs' ",
            "default": "en",
        },
        "calendar_percentage": {
            "label": "How much of the module should the calendar take up. Float between 0.0 and 1.0 ",
            "default": "0.5",
        },
        "event_fontsize": {
            "label": "Font size for the events (if 'show_events' arg is True) ",
            "default": "18",
        },
    }

    def __init__(self, config):
        """Initialize inkycal_gcalendar module"""

        super().__init__(config)
        config = config["config"]

        # optional parameters
        self.weekstart = config.get(
            "week_starts_on", GoogleCalendar.optional["week_starts_on"]["default"]
        )
        self.show_events = config.get(
            "show_events", GoogleCalendar.optional["show_events"]["default"]
        )
        self.date_format = config.get(
            "date_format", GoogleCalendar.optional["date_format"]["default"]
        )
        self.time_format = config.get(
            "time_format", GoogleCalendar.optional["time_format"]["default"]
        )
        self.language = config.get(
            "language", GoogleCalendar.optional["language"]["default"]
        )
        self.calendar_pct = config.get(
            "calendar_percentage",
            GoogleCalendar.optional["calendar_percentage"]["default"],
        )
        self.event_fontsize = config.get(
            "event_fontsize", GoogleCalendar.optional["event_fontsize"]["default"]
        )

        self.calendar_ids = str(config["calendar_ids"]).split(",")
        self.credentials_file = config["credentials_file"]

        # additional configuration
        self.timezone = get_system_tz()
        self.num_font = ImageFont.truetype(
            fonts["NotoSans-SemiCondensed"], size=self.fontsize
        )
        self.event_font = ImageFont.truetype(
            fonts["NotoSansUI-Regular"], size=int(self.event_fontsize)
        )

        # give an OK message
        print(f"{filename} loaded")

    def generate_image(self):
        """Generate image for this module"""

        # Define new image size with respect to padding
        im_width = int(self.width - (2 * self.padding_left))
        im_height = int(self.height - (2 * self.padding_top))
        im_size = im_width, im_height

        logger.info(f"Image size: {im_size}")

        # Create an image for black pixels and one for coloured pixels
        im_black = Image.new("RGB", size=im_size, color="white")
        im_colour = Image.new("RGB", size=im_size, color="white")

        #   column1                 column2
        # |-----------------------|----------|
        # |      Month Name       |Event 1   |
        # |Sun Mon Tue Wed Thu Fri|Event 2   |
        # |  1   2   3   4   5   6|Event 3   |
        # |  7   8   9  10  11  12|Event 4   |
        # |-----------------------|----------|

        # Allocate space for month-names, weekdays etc.
        month_name_height = int(im_height * 0.10)
        weekdays_height = int(self.font.getsize("hg")[1] * 1.25)
        logger.debug(f"month_name_height: {month_name_height}")
        logger.debug(f"weekdays_height: {weekdays_height}")

        calendar_width = int(im_width * float(self.calendar_pct))
        events_width = im_width - calendar_width
        # calendar_width = int(im_width / 2)
        # events_width = int(im_width / 2)
        calendar_height = im_height - month_name_height - weekdays_height
        events_height = im_height
        logger.info(f"calendar-section size: {calendar_width} x {calendar_height} px")
        logger.info(f"events-section size: {events_width} x {events_height} px")

        # Create a 7x6 grid and calculate icon sizes
        calendar_rows, calendar_cols = 6, 7
        icon_width = calendar_width // calendar_cols
        icon_height = calendar_height // calendar_rows
        logger.debug(f"icon_size: {icon_width}x{icon_height}px")

        # Calculate spacings for calendar area
        x_spacing_calendar = int((calendar_width % calendar_cols) / 2)
        y_spacing_calendar = int((im_height % calendar_rows) / 2)

        logger.debug(f"x_spacing_calendar: {x_spacing_calendar}")
        logger.debug(f"y_spacing_calendar :{y_spacing_calendar}")

        # Calculate positions for days of month
        grid_start_y = month_name_height + weekdays_height + y_spacing_calendar
        grid_start_x = x_spacing_calendar

        grid_coordinates = [
            (grid_start_x + icon_width * x, grid_start_y + icon_height * y)
            for y in range(calendar_rows)
            for x in range(calendar_cols)
        ]

        weekday_pos = [
            (grid_start_x + icon_width * _, month_name_height)
            for _ in range(calendar_cols)
        ]

        now = arrow.now(tz=self.timezone)

        # Set weekstart of calendar to specified weekstart
        if self.weekstart == "Monday":
            cal.setfirstweekday(cal.MONDAY)
            weekstart = now.shift(days=-now.weekday())
        else:
            cal.setfirstweekday(cal.SUNDAY)
            weekstart = now.shift(days=-now.isoweekday())

        # Write the name of current month
        write(
            im_black,
            (0, 0),
            (calendar_width, month_name_height),
            str(now.format("MMMM", locale=self.language)),
            font=self.font,
            autofit=True,
        )

        # Set up weeknames in local language and add to main section
        weekday_names = [
            weekstart.shift(days=+_).format("ddd", locale=self.language)
            for _ in range(7)
        ]
        logger.debug(f"weekday names: {weekday_names}")

        for _ in range(len(weekday_pos)):
            write(
                im_black,
                weekday_pos[_],
                (icon_width, weekdays_height),
                weekday_names[_],
                font=self.font,
                autofit=True,
                fill_height=1.0,
            )

        # Create a calendar template and flatten (remove nestings)
        flatten = lambda z: [x for y in z for x in y]
        calendar_flat = flatten(cal.monthcalendar(now.year, now.month))
        # logger.debug(f" calendar_flat: {calendar_flat}")

        # Map days of month to co-ordinates of grid -> 3: (row2_x,col3_y)
        grid = {}
        for i in calendar_flat:
            if i != 0:
                grid[i] = grid_coordinates[calendar_flat.index(i)]
        # logger.debug(f"grid:{grid}")

        # remove zeros from calendar since they are not required
        calendar_flat = [num for num in calendar_flat if num != 0]

        # Add the numbers on the correct positions
        for number in calendar_flat:
            if number != int(now.day):
                write(
                    im_black,
                    grid[number],
                    (icon_width, icon_height),
                    str(number),
                    font=self.num_font,
                    fill_height=0.5,
                    fill_width=0.5,
                )

        # Draw a red/black circle with the current day of month in white
        icon = Image.new("RGBA", (icon_width, icon_height))
        current_day_pos = grid[int(now.day)]
        x_circle, y_circle = int(icon_width / 2), int(icon_height / 2)
        radius = int(icon_width * 0.2)
        ImageDraw.Draw(icon).ellipse(
            (
                x_circle - radius,
                y_circle - radius,
                x_circle + radius,
                y_circle + radius,
            ),
            fill="black",
            outline=None,
        )
        write(
            icon,
            (0, 0),
            (icon_width, icon_height),
            str(now.day),
            font=self.num_font,
            fill_height=0.5,
            colour="white",
        )
        im_colour.paste(icon, current_day_pos, icon)

        # If events should be loaded and shown...
        if self.show_events:
            # find out how many lines can fit at max in the event section
            line_spacing = 0
            max_event_lines = events_height // (
                self.event_font.getsize("hg")[1] + line_spacing
            )

            # generate list of coordinates for each line
            events_offset = im_width - events_width + self.padding_left
            event_lines = [
                (events_offset, int(events_height / max_event_lines * _))
                for _ in range(max_event_lines)
            ]

            # logger.debug(f"event_lines {event_lines}")

            # timeline for filtering events within this month
            month_start = arrow.get(now.floor("month"))
            month_end = arrow.get(now.ceil("month"))

            # Filter events for full month (even past ones) for drawing event icons
            all_events = get_events(
                self.calendar_ids[0],
                month_start,
                credentials_file=self.credentials_file,
            )
            month_events = filter_events(all_events, month_start, month_end)
            upcoming_events = filter_events(all_events, now, now.shift(days=60))

            # find out on which days of this month events are taking place
            days_with_events = [
                int(events.start_time.format("D")) for events in month_events
            ]

            # remove duplicates (more than one event in a single day)
            list(set(days_with_events)).sort()

            # Draw a border with specified parameters around days with events
            for days in days_with_events:
                if days in grid:
                    draw_border(
                        im_colour,
                        grid[days],
                        (icon_width, icon_height),
                        radius=6,
                        thickness=1,
                        shrinkage=(0.4, 0.2),
                    )

            # delete events which won't be able to fit (more events than lines)
            upcoming_events = upcoming_events[:max_event_lines]

            # Check if any events were found in the given timerange
            if upcoming_events:

                # Find out how much space (width) the date format requires
                lang = self.language

                date_width = int(
                    max(
                        [
                            self.event_font.getsize(
                                events.start_time.format(self.date_format)
                            )[0]
                            for events in upcoming_events
                        ]
                    )
                    * 1.1
                )

                time_width = int(
                    max(
                        [
                            self.event_font.getsize(
                                events.start_time.format(self.time_format)
                            )[0]
                            for events in upcoming_events
                        ]
                    )
                    * 1.1
                )

                line_height = self.event_font.getsize("hg")[1] + line_spacing

                event_width = events_width - date_width - time_width

                cursor = 0
                future_date_label_created = False
                future_date_boundary = now.shift(days=21)
                for event in upcoming_events:
                    if cursor < len(event_lines):
                        event_name = event.summary
                        event_date = event.start_time.format(self.date_format)
                        event_time = event.start_time.format(self.time_format)
                        # logger.debug(f"name:{name}   date:{date} time:{time}")

                        if now < event.end_time:
                            # bold events that are today
                            bold = (
                                event.start_time.floor("day")
                                < now
                                < event.end_time.ceil("day")
                            )
                            if (
                                not future_date_label_created
                                and event.start_time > future_date_boundary
                            ):
                                write(
                                    im_colour,
                                    event_lines[cursor],
                                    (events_width, line_height + 5),
                                    "Future Events",
                                    font=self.event_font,
                                    alignment="left",
                                    underline=True,
                                )
                                future_date_label_created = True
                                cursor += 1

                            write(
                                im_colour,
                                event_lines[cursor],
                                (date_width, line_height),
                                event_date,
                                font=self.event_font,
                                alignment="left",
                                bold=bold,
                            )

                            # Check if event is all day
                            if event.is_all_day:
                                event_time = "     "
                            write(
                                im_black,
                                (
                                    event_lines[cursor][0] + date_width,
                                    event_lines[cursor][1],
                                ),
                                (time_width, line_height),
                                event_time,
                                font=self.event_font,
                                alignment="left",
                                bold=bold,
                            )

                            write(
                                im_black,
                                (
                                    event_lines[cursor][0] + date_width + time_width,
                                    event_lines[cursor][1],
                                ),
                                (event_width, line_height),
                                event_name,
                                font=self.event_font,
                                alignment="left",
                                bold=bold,
                            )
                            cursor += 1
            else:
                symbol = "- "
                while self.event_font.getsize(symbol)[0] < calendar_width * 0.9:
                    symbol += " -"
                write(
                    im_black,
                    event_lines[0],
                    (calendar_width, self.event_font.getsize(symbol)[1]),
                    symbol,
                    font=self.event_font,
                )

        # return the images ready for the display
        return im_black, im_colour


if __name__ == "__main__":
    print(f"running {filename} in standalone mode")
