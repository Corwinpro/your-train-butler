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


def train_status_update(context: CallbackContext) -> None:
    """Send the message about the railway service disruption."""
    job = context.job
    chat_id, _from, _to = job.context
    departure_status = next_departure_status(_from, _to)

    if departure_status.is_delayed or departure_status.is_cancelled:
        context.bot.send_message(chat_id, text=f"{departure_status!r}")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def subscribe_departure(update: Update, context: CallbackContext):
    _from, _to, *_ = context.args

    due = 5
    chat_id = update.message.chat_id

    job_name = f"{chat_id}-{_from.lower()}-{_to.lower()}"

    job_removed = remove_job_if_exists(job_name, context)

    context.job_queue.run_repeating(
        train_status_update, due, context=(chat_id, _from, _to), name=job_name
    )

    text = f"Subscribed to updates between {_from} and {_to}."
    if job_removed:
        text += " Old subscription was removed."
    update.message.reply_text(text)


dispatcher.add_handler(CommandHandler("subscribe", subscribe_departure))


def unsubscribe_departure(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
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

# updater.start_polling()
updater.start_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TELEGRAM_TOKEN,
    webhook_url="https://train-check.herokuapp.com/" + TELEGRAM_TOKEN,
)

logger.info("Webhook started.")

updater.idle()
