import logging

from telegram import BotCommand, Update
from telegram.ext import CallbackContext, CommandHandler

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
        text = (
            "To see all live departures from a station, use <code>/board ABC</code>"
            ", where ABC is the station code.\n"
            "To see live departures from one station to another station, use "
            "<code>/board ABC DEF</code>, where ABC and DEF are the origin and "
            "destination station codes."
        )
        update.message.reply_html(text)
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=departure_board(origin, destination, rows),
    )


def board_handler():
    command = "board"
    description = "Live departures board."
    return CommandHandler(command, send_departure_board), BotCommand(
        command, description
    )
