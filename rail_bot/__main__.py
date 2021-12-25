import logging
import os

from telegram.ext import Updater

from rail_bot.bot.start_handler import start_handler
from rail_bot.bot.board_handler import board_handler
from rail_bot.bot.departure_subscription import subscribe_handler, unsubscribe_handler
from rail_bot.bot.unknown_handler import unknown_command_handler
from rail_bot.bot.job_recovery import recover_jobs
from rail_bot.bot.help_handler import help_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8443))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# updater.start_webhook(
#     listen="0.0.0.0",
#     port=PORT,
#     url_path=TELEGRAM_TOKEN,
#     webhook_url="https://train-check.herokuapp.com/" + TELEGRAM_TOKEN,
# )
# logger.info("Webhook started.")


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

def test_but(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data='1'),
            InlineKeyboardButton("Option 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text=f"Selected option: {query.data}")

def main():
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    logger.info("Created Updater.")

    recover_jobs(updater.job_queue)

    dispatcher.add_handler(start_handler())
    dispatcher.add_handler(board_handler())
    dispatcher.add_handler(subscribe_handler())
    dispatcher.add_handler(unsubscribe_handler())
    dispatcher.add_handler(help_handler())

    updater.dispatcher.add_handler(CommandHandler('test', test_but))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # Must go very last
    dispatcher.add_handler(unknown_command_handler())

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
