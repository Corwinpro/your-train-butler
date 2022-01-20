import logging
import os
from typing import List

from telegram import Bot, BotCommand
from telegram.ext import Dispatcher, Updater

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
    dispatcher: Dispatcher = updater.dispatcher
    bot: Bot = dispatcher.bot
    bot_commands: List[BotCommand] = []

    logger.info("Created Updater.")

    service = create_subscription_service()
    job_manager = JobManager(job_queue=updater.job_queue, service=service)

    job_manager.recover_travel_jobs()

    # Add /start handler
    dispatcher.add_handler(start_handler())

    # Add /board handler and bot commands
    board_handler_, board_bot_command = board_handler()
    dispatcher.add_handler(board_handler_)
    bot_commands.append(board_bot_command)

    # Add /subscribe handler and bot commands
    subscribe_handler_, subscribe_bot_command = subscribe_handler(job_manager)
    dispatcher.add_handler(subscribe_handler_)
    bot_commands.append(subscribe_bot_command)

    # Add /unsubscribe handler and bot commands
    for handler, bot_command in unsubscribe_handler(job_manager):
        dispatcher.add_handler(handler)
        if bot_command is not None:
            bot_commands.append(bot_command)

    # Add /help handler and bot commands
    help_handler_, bot_help_command = help_handler()
    dispatcher.add_handler(help_handler_)
    bot_commands.append(bot_help_command)

    # Must go very last
    dispatcher.add_handler(unknown_command_handler())

    # Set the bot commands
    bot.set_my_commands(bot_commands)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
