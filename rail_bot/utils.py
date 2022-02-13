import datetime


def parse_time(time: str) -> datetime.time:
    date_time = datetime.datetime.strptime(time, "%H:%M")
    return datetime.time(hour=date_time.hour, minute=date_time.minute)


def shift_time(
    time_from: datetime.time, delta_hour: int = 0, delta_minute: int = 0
) -> datetime.time:
    delta = datetime.timedelta(hours=delta_hour, minutes=delta_minute)

    new_time = (
        datetime.datetime.combine(datetime.date.today(), time_from) + delta
    ).time()
    return new_time
