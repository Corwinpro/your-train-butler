from telegram.ext import CallbackContext, CommandHandler
from telegram import Update


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"You are {update.effective_user.id}"
    )


def start_handler():
    return CommandHandler("start", start)
