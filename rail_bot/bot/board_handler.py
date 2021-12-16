from telegram.ext import CallbackContext, CommandHandler
from telegram import Update

from rail_bot.rail_api import departure_board


def send_departure_board(update: Update, context: CallbackContext):
    destination = None
    rows = 10
    if len(context.args) == 1:
        origin = context.args[0]
    elif len(context.args) == 2:
        origin, destination = context.args
    elif len(context.args) == 3:
        origin, destination, rows = context.args

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=departure_board(origin, destination, rows),
    )


def board_handler():
    return CommandHandler("board", send_departure_board)
