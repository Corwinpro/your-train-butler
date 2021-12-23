from telegram.ext import CallbackContext, CommandHandler
from telegram import Update


def help(update: Update, context: CallbackContext):
    text = """
    \#\#\# Train Check Bot 🚂
    Train Check Bot can:
    \- Tell you about live departures from a station:

    \> /board KGX

    or between stations:

    \> /board KGX CBG

    \- Notify you about service disruptions. To recieve notifications in case
      anything goes wrong, subscribe to a service update via:

    \> /subscribe KGX CBG 12:23
    """
    update.message.reply_markdown_v2(text)


def help_handler():
    return CommandHandler("help", help)
