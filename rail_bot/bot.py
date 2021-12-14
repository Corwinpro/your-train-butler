import datetime
import logging
import os

from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Updater,
    MessageHandler,
    Filters,
)
from telegram import Update

from rail_bot.rail_api import departure_board, next_departure_status

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8443))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher

logger.info("Created Updater.")

def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"You are {update.effective_user.id}"
    )


dispatcher.add_handler(CommandHandler("start", start))


def send_departure_board(update: Update, context: CallbackContext):
    _to = None
    rows = 10
    if len(context.args) == 1:
        _from = context.args[0]
    elif len(context.args) == 2:
        _from, _to = context.args
    elif len(context.args) == 3:
        _from, _to, rows = context.args

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=departure_board(_from, _to, rows),
    )


dispatcher.add_handler(CommandHandler("board", send_departure_board))


def initiate_status_check(context: CallbackContext) -> None:
    """Send the message about the railway service disruption."""
    chat_id, origin, destination, time = context.job.context
    logger.info(f"initiate_status_check: {context.job.context}")
    departure_status = next_departure_status(origin, destination)

    context.bot.send_message(chat_id, text=f"DEBUG: {departure_status!r}")

    if departure_status.is_delayed or departure_status.is_cancelled:
        context.bot.send_message(chat_id, text=f"{departure_status!r}")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    logger.info(f"{name} " + ", ".join([job.name for job in context.job_queue.jobs()]))
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def _parse_time(time):
    date_time = datetime.datetime.strptime(time, "%H:%M")
    return datetime.time(hour=date_time.hour, minute=date_time.minute)


def subscribe_departure_job_name(chat_id, origin, destination, departure_time):
    return f"{chat_id}-{origin.lower()}-{destination.lower()}-{departure_time}"


def subscribe_departure(update: Update, context: CallbackContext):
    origin, destination, departure_time = context.args
    try:
        departure_time = _parse_time(departure_time)
    except Exception as e:
        update.message.reply_text(f"{e!r}")
        return

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
    first_check_time = datetime.time(
        *divmod(first_check_time_seconds // 60, 60)
    )

    # only on weekdays
    days=tuple(range(5))

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


dispatcher.add_handler(CommandHandler("subscribe", subscribe_departure))


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


dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe_departure))


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


dispatcher.add_handler(MessageHandler(Filters.command, unknown))

updater.start_polling()
# updater.start_webhook(
#     listen="0.0.0.0",
#     port=PORT,
#     url_path=TELEGRAM_TOKEN,
#     webhook_url="https://train-check.herokuapp.com/" + TELEGRAM_TOKEN,
# )
# logger.info("Webhook started.")

updater.idle()
