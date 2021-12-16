from telegram.ext import CallbackContext, MessageHandler, Filters
from telegram import Update


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def unknown_command_handler():
    return MessageHandler(Filters.command, unknown)
