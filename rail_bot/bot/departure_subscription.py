import functools
import datetime
import logging

from telegram.ext import CallbackContext, CommandHandler
from telegram import Update

from rail_bot.bot.utils import parse_time
from rail_bot.bot.job_manager import remove_job_if_exists
from rail_bot.rail_api import next_departure_status


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


def subscribe_departure_job_name(chat_id, origin, destination, departure_time):
    return f"{chat_id}-{origin.lower()}-{destination.lower()}-{departure_time}"


def initiate_status_check(context: CallbackContext) -> None:
    """Send the message about the railway service disruption."""
    chat_id, origin, destination, time = context.job.context
    logger.info(f"initiate_status_check: {context.job.context}")
    departure_status = next_departure_status(origin, destination)

    context.bot.send_message(chat_id, text=f"DEBUG: {departure_status!r}")

    if departure_status.is_delayed or departure_status.is_cancelled:
        context.bot.send_message(chat_id, text=f"{departure_status!r}")


@parse_subscription_info
def subscribe_departure(update: Update, context: CallbackContext):
    origin, destination, departure_time = context.args

    chat_id = update.message.chat_id
    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )

    job_removed = remove_job_if_exists(job_name, context)

    # The scheduled departure check is initiated some time before the departure
    delta_before_departure = datetime.time(hour=1)
    first_check_time_seconds = (
        datetime.datetime.combine(datetime.date.min, departure_time)
        - datetime.datetime.combine(datetime.date.min, delta_before_departure)
    ).seconds
    first_check_time = datetime.time(*divmod(first_check_time_seconds // 60, 60))

    # only on weekdays
    days = tuple(range(5))

    context.job_queue.run_daily(
        initiate_status_check,
        time=first_check_time,
        days=days,
        context=(chat_id, origin, destination, departure_time),
        name=job_name,
    )

    text = (
        f"Subscribed to updates between {origin.upper()} and "
        f"{destination.upper()} at {departure_time}."
    )
    if job_removed:
        text += " Old subscription was removed."
    update.message.reply_text(text)


@parse_subscription_info
def unsubscribe_departure(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    origin, destination, departure_time = context.args

    chat_id = update.message.chat_id
    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )
    job_removed = remove_job_if_exists(job_name, context)
    if job_removed:
        text = "Subscription cancelled!"
    else:
        text = "You have no active subscriptions."
    update.message.reply_text(text)


def subscribe_handler():
    return CommandHandler("subscribe", subscribe_departure)


def unsubscribe_handler():
    return CommandHandler("unsubscribe", unsubscribe_departure)
