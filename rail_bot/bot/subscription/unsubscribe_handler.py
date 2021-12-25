import logging

from telegram.ext import CallbackContext, CommandHandler
from telegram import Update
from telegram.ext.jobqueue import JobQueue
from rail_bot.bot.service.job_service import create_job_service
from rail_bot.bot.subscription.common import UNSUBSCRIBE, subscribe_departure_job_name

from rail_bot.bot.utils import parse_time
from rail_bot.bot.job_manager import remove_jobs_by_prefix


logger = logging.getLogger(__name__)


UNSUBSCRIBE = "unsubscribe"


def unsubscribe_info(chat_id: int) -> str:
    job_service = create_job_service()

    active_jobs = job_service.get_jobs(chat_id=chat_id)
    if len(active_jobs) == 0:
        return "You have no subscriptions."

    text = f"You have {len(active_jobs)} subscriptions:\n"
    for job in sorted(active_jobs, key=lambda job: job.departure_time):
        time = f"{job.departure_time.hour}:{job.departure_time.minute}"
        text += (
            f"- From {job.origin.upper()} to {job.destination.upper()} at {time}\n"
        )
    text += (
        "Use <code>/unsubscibe ORIGIN DESTINATION HH:MM</code> to unsubscribe"
        f" from a service update, or <code>/{UNSUBSCRIBE} all</code> to cancel"
        " all notifications."
    )
    return text


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
    chat_id: int, origin: str, destination: str, departure_time_str: str, job_queue: JobQueue
) -> str:

    departure_time = parse_time(departure_time_str)

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
    if len(context.args) == 0:
        response = unsubscribe_info(chat_id)
    elif len(context.args) == 1:
        response = unsubscribe_all(chat_id, context.args[0], context.job_queue)
    elif len(context.args) == 3:
        origin, destination, departure_time = context.args
        response = unsubscribe_one(
            chat_id, origin, destination, departure_time, context.job_queue
        )
    update.message.reply_html(response)


def unsubscribe_handler():
    return CommandHandler(UNSUBSCRIBE, _unsubscribe_departure)
