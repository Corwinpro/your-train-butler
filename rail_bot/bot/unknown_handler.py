from telegram import Update
from telegram.ext import CallbackContext, Filters, MessageHandler


def unknown(update: Update, context: CallbackContext):
    if update.effective_chat is None:
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def unknown_command_handler():
    return MessageHandler(Filters.command, unknown)
