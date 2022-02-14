from typing import Union
import datetime

HOUR_MINUTE_FORMAT = "%H:%M"


def parse_time(time: str) -> datetime.time:
    date_time = datetime.datetime.strptime(time, HOUR_MINUTE_FORMAT)
    return datetime.time(hour=date_time.hour, minute=date_time.minute)


def format_time(time: Union[datetime.time, str]) -> str:
    if isinstance(time, str):
        return time

    return time.strftime(HOUR_MINUTE_FORMAT)


def shift_time(
    time_from: datetime.time, delta_hour: int = 0, delta_minute: int = 0
) -> datetime.time:
    delta = datetime.timedelta(hours=delta_hour, minutes=delta_minute)

    new_time = (
        datetime.datetime.combine(datetime.date.today(), time_from) + delta
    ).time()
    return new_time
