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


logger = logging.getLogger(__name__)


def parse_subscription_info(func: Callable[[Update, CallbackContext], None]):
    @functools.wraps(func)
    def wrapped(update: Update, context: CallbackContext):
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

        context.args[2] = departure_time

        func(update, context)

    return wrapped


def subscribe_departure_job_name(
    chat_id: int, origin: str, destination: str, departure_time: datetime.time
) -> str:
    return f"{chat_id}-{origin.lower()}-{destination.lower()}-{departure_time}"


def get_travel_status(context: CallbackContext) -> None:
    """ Get current departure status, and compare it to the already known one
    from some time ago. If there are any changes, report to the user.

    Submit this function to run again in some time.

    This function is executed in a JobQueue.
    """
    logger.info(f"get_travel_status: {context.job.context}")

    chat_id, origin, destination, time, travel_obj = context.job.context

    current_time = datetime.datetime.now()
    if current_time > datetime.datetime.combine(datetime.date.today(), time):
        # Already too late
        return

    current_travel_obj = next_departure_status(origin, destination)

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


def initiate_status_check(context: CallbackContext) -> None:
    """Initiate a sequence of checks for railway service disruption.

    This function is executed in a JobQueue.
    """
    chat_id, origin, destination, time = context.job.context
    logger.info(f"initiate_status_check: {context.job.context}")

    job_name = (
        subscribe_departure_job_name(chat_id, origin, destination, time)
        + f"-{datetime.datetime.now()}"
    )
    context.job_queue.run_once(
        get_travel_status,
        when=1,
        context=(chat_id, origin, destination, time, None),
        name=job_name,
    )


def subscribe_departure(
    job_queue: JobQueue,
    chat_id: int,
    origin: str,
    destination: str,
    departure_time: datetime.time,
):
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
        initiate_status_check,
        time=first_check_time,
        days=days,
        context=(chat_id, origin, destination, departure_time),
        name=job_name,
    )

    response = (
        f"Subscribed to updates between {origin.upper()} and {destination.upper()}"
        f" at {departure_time}."
    )
    if job_removed:
        response += " Old subscription was removed."

    if first_check_time < datetime_now.time() < departure_time:
        job_queue.run_once(
            callback=initiate_status_check,
            when=1,
            context=(chat_id, origin, destination, departure_time),
            name=job_name + f"-{datetime_now}",
        )

    return response


@parse_subscription_info
def _subscribe_departure(update: Update, context: CallbackContext) -> None:
    origin, destination, departure_time = context.args

    job_service = create_job_service()
    job_service.add_job(
        chat_id=update.message.chat_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
    )

    response = subscribe_departure(
        context.job_queue, update.message.chat_id, *context.args
    )
    update.message.reply_text(response)


def _unsubscribe_departure(update: Update, context: CallbackContext) -> None:
    """ Remove the job if the user changed their mind."""
    job_service = create_job_service()
    chat_id = update.message.chat_id

    if len(context.args) == 0:
        active_jobs = job_service.get_jobs(chat_id=chat_id)
        if len(active_jobs) == 0:
            update.message.reply_text("You have no subscriptions.")
            return

        text = f"You have {len(active_jobs)} subscriptions:\n"
        for job in active_jobs:
            time = f"{job.departure_time.hour}:{job.departure_time.minute}"
            text += f"- From {job.origin.upper()} to {job.destination.upper()} at {time}\n"
        text += "To unsubscribe, type:\n <code>/unsubscibe ORIGIN DESTINATION HH:MM</code>."
        update.message.reply_html(text)
        return

    origin, destination, departure_time = context.args
    departure_time = parse_time(departure_time)

    job_service.deactivate_job(
        chat_id=chat_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
    )

    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )
    job_removed = remove_jobs_by_prefix(job_name, context.job_queue)
    if job_removed:
        text = (
            f"Subscription from {origin} to {destination} at {departure_time} "
            "cancelled!"
        )
    else:
        text = (
            f"I could not find subscriptions to the service between {origin} "
            f" and {destination} at {departure_time}. See <code>/unsubscribe</code>"
            f" for more information about your subscriptions."
        )
    update.message.reply_html(text)


def subscribe_handler():
    return CommandHandler("subscribe", _subscribe_departure)


def unsubscribe_handler():
    return CommandHandler("unsubscribe", _unsubscribe_departure)
