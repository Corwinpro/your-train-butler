import functools
import datetime
import logging
from typing import Callable

from telegram.ext import CallbackContext, CommandHandler
from telegram import Update
from telegram.ext.jobqueue import JobQueue
from rail_bot.bot.service.job_service import create_job_service

from rail_bot.bot.utils import parse_time, shift_time
from rail_bot.bot.job_manager import remove_jobs_by_prefix
from rail_bot.rail_api.api import next_departure_status
from rail_bot.bot.subscription.common import SUBSCRIBE, subscribe_departure_job_name

logger = logging.getLogger(__name__)


def parse_subscription_info(
    func: Callable[[JobQueue, int, str, str, datetime.time], str]
):
    @functools.wraps(func)
    def wrapped(update: Update, context: CallbackContext):
        chat_id = update.message.chat_id

        if context.args is None:
            logger.info(f"Got `None` as context.args in `{func}` with {chat_id}.")
            return

        if context.job_queue is None:
            logger.info(f"Got `None` as context.job_queue in `{func}` with {chat_id}.")
            return

        try:
            origin, destination, departure_time = context.args
        except ValueError:
            update.message.reply_text(
                f"Subscribe to service updates by specifying "
                f"\n-The origin of your travel (e.g., 'kgx'),"
                f"\n-The destination of your travel (e.g., 'cbg'),"
                f"\n-Departure time (e.g., '12:23')."
            )
            return

        try:
            departure_time = parse_time(departure_time)
        except Exception as e:
            update.message.reply_text(f"{e!r}")
            return

        job_queue = context.job_queue

        response = func(job_queue, chat_id, origin, destination, departure_time)
        update.message.reply_text(response)

    return wrapped


def get_travel_status(context: CallbackContext) -> None:
    """Get current departure status, and compare it to the already known one
    from some time ago. If there are any changes, report to the user.

    Submit this function to run again in some time.

    This function is executed in a JobQueue.
    """
    if context.job is None:
        logger.info(f"Got `None` as context.job in `get_travel_status`.")
        return

    if context.job_queue is None:
        logger.info(f"Got `None` as context.job_queue in `get_travel_status`.")
        return

    logger.info(f"get_travel_status: {context.job.context}")

    chat_id, origin, destination, time, travel_obj = context.job.context

    current_time = datetime.datetime.now()
    if current_time > datetime.datetime.combine(datetime.date.today(), time):
        # Already too late
        return

    current_travel_obj = next_departure_status(origin, destination)
    if current_travel_obj is None:
        text = "❗ It seems that your travel has been cancelled. ❗\n"
        text += "I am sorry I could not find any additional information."
        context.bot.send_message(chat_id, text=text)
        return

    if current_travel_obj.is_delayed or current_travel_obj.is_cancelled:
        rerun_in = 2 * 60  # seconds

        if current_travel_obj != travel_obj:
            context.bot.send_message(chat_id, text=f"{current_travel_obj!r}")
    else:
        rerun_in = 10 * 60  # seconds

    job_name = (
        subscribe_departure_job_name(chat_id, origin, destination, time)
        + f"-{current_time}"
    )
    context.job_queue.run_once(
        get_travel_status,
        when=rerun_in,
        context=(chat_id, origin, destination, time, current_travel_obj),
        name=job_name,
    )


def subscribe_departure(
    job_queue: JobQueue,
    chat_id: int,
    origin: str,
    destination: str,
    departure_time: datetime.time,
) -> str:
    datetime_now = datetime.datetime.now()
    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )

    job_removed = remove_jobs_by_prefix(job_name, job_queue)

    # The scheduled departure check is initiated some time before the departure
    first_check_time = shift_time(departure_time, delta_hour=-1, delta_minute=0)

    # only on weekdays
    days = tuple(range(7))

    job_queue.run_daily(
        get_travel_status,
        time=first_check_time,
        days=days,
        context=(chat_id, origin, destination, departure_time, None),
        name=job_name,
    )

    response = (
        f"Subscribed to updates between {origin.upper()} and {destination.upper()}"
        f" at {departure_time}."
    )
    if job_removed != 0:
        response += " Old subscription was removed."

    if first_check_time < datetime_now.time() < departure_time:
        job_queue.run_once(
            callback=get_travel_status,
            when=1,
            context=(chat_id, origin, destination, departure_time, None),
            name=job_name + f"-{datetime_now}",
        )

    return response


@parse_subscription_info
def _subscribe_departure(
    job_queue: JobQueue,
    chat_id: int,
    origin: str,
    destination: str,
    departure_time: datetime.time,
) -> str:

    job_service = create_job_service()
    job_service.add_job(
        chat_id=chat_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
    )

    response = subscribe_departure(
        job_queue, chat_id, origin, destination, departure_time
    )
    return response


def subscribe_handler():
    return CommandHandler(SUBSCRIBE, _subscribe_departure)