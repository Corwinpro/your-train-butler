import logging
import os

from telegram.ext import Updater

from rail_bot.bot.board_handler import board_handler
from rail_bot.bot.help_handler import help_handler
from rail_bot.bot.job_manager import JobManager
from rail_bot.bot.service.subscription_service import create_subscription_service
from rail_bot.bot.start_handler import start_handler
from rail_bot.bot.subscription.subscribe_handler import subscribe_handler
from rail_bot.bot.subscription.unsubscribe_handler import unsubscribe_handler
from rail_bot.bot.unknown_handler import unknown_command_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8443))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")


def main():
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    logger.info("Created Updater.")

    service = create_subscription_service()
    job_manager = JobManager(job_queue=updater.job_queue, service=service)

    job_manager.recover_travel_jobs()

    dispatcher.add_handler(start_handler())
    dispatcher.add_handler(board_handler())
    dispatcher.add_handler(subscribe_handler(job_manager))
    for handler in unsubscribe_handler(job_manager):
        dispatcher.add_handler(handler)
    dispatcher.add_handler(help_handler())

    # Must go very last
    dispatcher.add_handler(unknown_command_handler())

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
