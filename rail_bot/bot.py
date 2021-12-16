import logging
import os

from telegram.ext import Updater

from rail_bot.bot.start_handler import start_handler
from rail_bot.bot.board_handler import board_handler
from rail_bot.bot.departure_subscription import subscribe_handler, unsubscribe_handler
from rail_bot.bot.unknown_handler import unknown_command_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8443))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher

logger.info("Created Updater.")

dispatcher.add_handler(start_handler())
dispatcher.add_handler(board_handler())
dispatcher.add_handler(subscribe_handler())
dispatcher.add_handler(unsubscribe_handler())
dispatcher.add_handler(unknown_command_handler())

updater.start_polling()
updater.idle()


# def alarm(context: CallbackContext) -> None:
#     """Send the alarm message."""
#     chat_id = 50179005
#     context.bot.send_message(chat_id, text="DEBUG: HELLO")

# updater.job_queue.run_repeating(alarm, 5)

# updater.start_webhook(
#     listen="0.0.0.0",
#     port=PORT,
#     url_path=TELEGRAM_TOKEN,
#     webhook_url="https://train-check.herokuapp.com/" + TELEGRAM_TOKEN,
# )
# logger.info("Webhook started.")
