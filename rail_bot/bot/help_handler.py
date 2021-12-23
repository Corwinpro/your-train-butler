from telegram.ext import CallbackContext, CommandHandler
from telegram import Update


def help(update: Update, context: CallbackContext):
    text = """
    <p>Train Check Bot 🚂</p>
    Train Check Bot can:
    <ul>
        <li> Tell you about live departures from a station:

            <blockquote>/board KGX</blockquote>

    or between stations:

        <blockquote>/board KGX CBG</blockquote>

    <li> Notify you about service disruptions. To recieve notifications in case
    anything goes wrong, subscribe to a service update via:

            <blockquote>/subscribe KGX CBG 12:23</blockquote>
    """
    update.message.reply_html(text)


def help_handler():
    return CommandHandler("help", help)
