from telegram.ext import CallbackContext, CommandHandler
from telegram import Update


def help(update: Update, context: CallbackContext):
    text = (
        "<b>Train Check Bot</b>🚂\n"
        "Train Check Bot can:\n"
        "- Tell you about live departures from a station:\n"
        "    <code>/board KGX</code>\n"
        "  or between stations:\n"
        "    <code>/board KGX CBG</code>\n"
        "- Notify you about service disruptions. "
        "To recieve notifications in case anything goes wrong, "
        "subscribe to a service update via\n"
        "  <code>/subscribe KGX CBG 12:23</code>"
    )
    update.message.reply_html(text)


def help_handler():
    return CommandHandler("help", help)
