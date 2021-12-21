import functools
import datetime
import logging

from telegram.ext import CallbackContext, CommandHandler
from telegram import Update
from telegram.ext.jobqueue import JobQueue
from rail_bot.bot.service.job_service import create_job_service

from rail_bot.bot.utils import parse_time
from rail_bot.bot.job_manager import remove_job_if_exists
from rail_bot.rail_api.api import next_departure_status


logger = logging.getLogger(__name__)


def parse_subscription_info(func):
    @functools.wraps(func)
    def wrapped(update: Update, context: CallbackContext):
        try:
            origin, destination, departure_time = context.args
        except ValueError:
            update.message.reply_text(f"Incorrect arguments.")
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
    """Get current departure status, and compare it to the already known one
    from some time ago. If there are any changes, report to the user.

    Submit this function to run again in some time.

    This function is executed in a JobQueue.
    """
    logger.info(f"initiate_status_check: {context.job.context}")

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
        + f"{current_time}"
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

    # departure_status = next_departure_status(origin, destination)
    # context.bot.send_message(chat_id, text=f"DEBUG: {departure_status!r}")
    # if departure_status.is_delayed or departure_status.is_cancelled:
    #     context.bot.send_message(chat_id, text=f"{departure_status!r}")

    job_name = (
        subscribe_departure_job_name(chat_id, origin, destination, time)
        + f"{datetime.datetime.now()}"
    )
    context.job_queue.run_once(
        get_travel_status,
        when=1,
        context=(chat_id, origin, destination, time, None),
        name=job_name,
    )


def _subtract_time(
    time_from: datetime.time, delta_hour: int = 0, delta_minute: int = 0
) -> datetime.time:
    delta_time = datetime.time(hour=delta_hour, minute=delta_minute)
    subtracted_time_seconds = (
        datetime.datetime.combine(datetime.date.min, time_from)
        - datetime.datetime.combine(datetime.date.min, delta_time)
    ).seconds
    subtracted_time = datetime.time(*divmod(subtracted_time_seconds // 60, 60))
    return subtracted_time


def subscribe_departure(
    job_queue: JobQueue,
    chat_id: int,
    origin: str,
    destination: str,
    departure_time: datetime.time,
):
    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )

    job_removed = remove_job_if_exists(job_name, job_queue)

    # The scheduled departure check is initiated some time before the departure
    first_check_time = _subtract_time(departure_time, delta_hour=1, delta_minute=0)

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


@parse_subscription_info
def _unsubscribe_departure(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    origin, destination, departure_time = context.args
    chat_id = update.message.chat_id

    job_service = create_job_service()
    job_service.deactivate_job(
        chat_id=update.message.chat_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
    )

    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )
    job_removed = remove_job_if_exists(job_name, context.job_queue)
    if job_removed:
        text = "Subscription cancelled!"
    else:
        text = "You have no active subscriptions."
    update.message.reply_text(text)


def subscribe_handler():
    return CommandHandler("subscribe", _subscribe_departure)


def unsubscribe_handler():
    return CommandHandler("unsubscribe", _unsubscribe_departure)
