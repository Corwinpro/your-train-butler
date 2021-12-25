import datetime
import logging
from typing import Optional, Tuple

from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext.jobqueue import JobQueue
from telegram.callbackquery import CallbackQuery

from rail_bot.bot.service.job_service import DailyJob, create_job_service
from rail_bot.bot.subscription.common import UNSUBSCRIBE, subscribe_departure_job_name

from rail_bot.bot.utils import parse_time
from rail_bot.bot.job_manager import remove_jobs_by_prefix


logger = logging.getLogger(__name__)


UNSUBSCRIBE = "unsubscribe"


def unsubscribe_button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query: CallbackQuery = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    if context.job_queue is None:
        return

    job: DailyJob = query.data
    unsubscribe_one(
        update.message.chat_id, job.origin, job.destination, job.departure_time, context.job_queue
    )

    time = f"{job.departure_time.hour}:{job.departure_time.minute}"
    query.edit_message_text(
        text=(
            f"Unsubscribed from:\nTravel from {job.origin.upper()} to "
            f"{job.destination.upper()} at {time}"
        )
    )


def unsubscribe_info(chat_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    job_service = create_job_service()

    active_jobs = job_service.get_jobs(chat_id=chat_id)
    if len(active_jobs) == 0:
        return "You have no subscriptions.", None

    text = f"You have {len(active_jobs)} subscriptions.\nClick to unsubscribe. "
    keyboard = []
    for job in sorted(active_jobs, key=lambda job: job.departure_time):
        time = f"{job.departure_time.hour}:{job.departure_time.minute}"
        key_text = (
            f"- From {job.origin.upper()} to {job.destination.upper()} at {time}\n"
        )
        keyboard.append([InlineKeyboardButton(key_text, callback_data=job)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text += (
        "Or, use <code>/unsubscibe ORIGIN DESTINATION HH:MM</code> to unsubscribe"
        f" from a service update, and <code>/{UNSUBSCRIBE} all</code> to cancel"
        " all notifications."
    )
    return text, reply_markup


def unsubscribe_all(chat_id: int, option: str, job_queue: JobQueue) -> str:
    if option == "all":
        job_service = create_job_service()
        job_service.deactivate_job(chat_id=chat_id)
        job_removed = remove_jobs_by_prefix(str(chat_id), job_queue)
        text = f"I cancelled {job_removed} subscriptions."
    else:
        text = (
            "Sorry, I cannot understand that. Did you want to unsubscribe from "
            f"all notifications? For that please use\n<code>/{UNSUBSCRIBE} all</code>"
        )
    return text


def unsubscribe_one(
    chat_id: int, origin: str, destination: str, departure_time: datetime.time, job_queue: JobQueue
) -> str:

    job_service = create_job_service()
    job_service.deactivate_job(
        chat_id=chat_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
    )

    job_name = subscribe_departure_job_name(
        chat_id, origin, destination, departure_time
    )
    job_removed = remove_jobs_by_prefix(job_name, job_queue)
    if job_removed != 0:
        text = (
            f"Subscription from {origin} to {destination} at {departure_time} "
            "cancelled!"
        )
    else:
        text = (
            f"I could not find subscriptions to the service between {origin} "
            f" and {destination} at {departure_time}. See <code>/{UNSUBSCRIBE}</code>"
            f" for more information about your subscriptions."
        )
    return text


def _unsubscribe_departure(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    if context.args is None:
        logger.info(f"Got `None` as context.args in {update.message.chat_id}.")
        return

    chat_id: int = update.message.chat_id

    if context.job_queue is None:
        logger.info(
            f"Got `None` as context.job_queue in `get_travel_status` with {chat_id}."
        )
        return

    response = "I am sorry I cannot understand that."
    markup = None
    if len(context.args) == 0:
        response, markup = unsubscribe_info(chat_id)
    elif len(context.args) == 1:
        response = unsubscribe_all(chat_id, context.args[0], context.job_queue)
    elif len(context.args) == 3:
        origin, destination, departure_time = context.args
        departure_time = parse_time(departure_time)
        response = unsubscribe_one(
            chat_id, origin, destination, departure_time, context.job_queue
        )
    update.message.reply_html(response, reply_markup=markup)


def unsubscribe_handler():
    CallbackQueryHandler(unsubscribe_button)
    return (
        CommandHandler(UNSUBSCRIBE, _unsubscribe_departure),
        CallbackQueryHandler(unsubscribe_button)
    )
