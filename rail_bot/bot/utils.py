import datetime


def parse_time(time):
    date_time = datetime.datetime.strptime(time, "%H:%M")
    return datetime.time(hour=date_time.hour, minute=date_time.minute)
