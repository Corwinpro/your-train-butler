from telegram.ext import CallbackContext, CommandHandler
from telegram import Update

from rail_bot.bot.subscription.common import UNSUBSCRIBE


def help(update: Update, context: CallbackContext):
    text = (
        "<b>Train Check Bot</b>🚂\n\n"
        "Hey there! I am your personal rail butler. I can:\n"
        "- Tell you about live departures from a particular station:\n\n"
        "    <code>/board KGX</code>\n\n"
        "  or between two stations:\n\n"
        "    <code>/board KGX CBG</code>\n\n"
        "- Notify you about service disruptions.\n"
        "  If you tell me which travels you would like to follow, I will "
        "notify you in case anything goes wrong with the train.\n"
        "  To subscribe to a service update, let me know about your origin "
        "station, your destination, and the departure time:\n\n"
        "  <code>/subscribe KGX CBG 12:23</code>\n\n"
        f"  To see all your subscriptions, type <code>/{UNSUBSCRIBE}</code>.\n"
        f"  To unsubscribe from a service, type  <code>/{UNSUBSCRIBE} KGX CBG 12:23</code>\n"
        f"  To unsubscribe from all notifications, type <code>/{UNSUBSCRIBE} all</code>"
    )
    update.message.reply_html(text)


def help_handler():
    return CommandHandler("help", help)
