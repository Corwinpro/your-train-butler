import logging

from telegram.ext import CallbackContext, CommandHandler
from telegram import Update

from rail_bot.rail_api.api import departure_board


logger = logging.getLogger(__name__)


def send_departure_board(update: Update, context: CallbackContext):
    if context.args is None:
        logger.info(
            f"Got `None` as context.args in `send_departure_board` with "
            f"{update.message.chat_id}."
        )
        return

    if update.effective_chat is None:
        logger.info(
            f"Got `None` as update.effective_chat in `send_departure_board` "
            f"with {update.message.chat_id}."
        )
        return

    destination = None
    rows = 10
    if len(context.args) == 1:
        origin = context.args[0]
    elif len(context.args) == 2:
        origin, destination = context.args
    elif len(context.args) == 3:
        origin, destination, rows = context.args
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "The '/board' command requires at least one argument: name"
                " of the station (e.g. 'KGX'). See /help for more info."
            ),
        )
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=departure_board(origin, destination, rows),
    )


def board_handler():
    return CommandHandler("board", send_departure_board)
