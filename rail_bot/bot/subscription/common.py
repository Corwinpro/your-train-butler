import datetime


UNSUBSCRIBE = "unsubscribe"
SUBSCRIBE = "subscribe"


def subscribe_departure_job_name(
    chat_id: int, origin: str, destination: str, departure_time: datetime.time
) -> str:
    return f"{chat_id}-{origin.lower()}-{destination.lower()}-{departure_time}"
