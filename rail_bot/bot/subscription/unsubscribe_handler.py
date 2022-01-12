import datetime
import logging
from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.callbackquery import CallbackQuery
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from rail_bot.bot.job_manager import JobManager
from rail_bot.bot.service.subscription_service import Travel
from rail_bot.bot.subscription.common import UNSUBSCRIBE
from rail_bot.bot.utils import parse_time

logger = logging.getLogger(__name__)


# TODO: callback data should be just travel_id
def travels_markup(travels: List[Travel]) -> InlineKeyboardMarkup:
    keyboard = []
    for travel in sorted(travels, key=lambda travel: travel.departure_time):
        time_str = (
            str(travel.departure_time.hour).zfill(2)
            + ":"
            + str(travel.departure_time.minute).zfill(2)
        )
        key_text = f"- From {travel.origin.upper()} to {travel.destination.upper()} at {time_str}"

        travel_data = " ".join((travel.origin, travel.destination, time_str))
        keyboard.append([InlineKeyboardButton(key_text, callback_data=travel_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


class UnsubscribeController:
    def __init__(self, job_manager: JobManager) -> None:
        self.job_manager = job_manager

    def unsubscribe_info(
        self, chat_id: int
    ) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
        active_subscriptions = self.job_manager.service.get_subscriptions(
            chat_id=chat_id
        )
        if len(active_subscriptions) == 0:
            return "You have no subscriptions.", None

        travels = [
            self.job_manager.service.get_travels(travel_id=subscription.travel_id)[0]
            for subscription in active_subscriptions
        ]
        text = (
            f"You have {len(active_subscriptions)} subscriptions.\nClick to unsubscribe. "
            f"Or use <code>/{UNSUBSCRIBE} ORIGIN DESTINATION HH:MM</code> to unsubscribe"
            f" from a service update, and <code>/{UNSUBSCRIBE} all</code> to cancel"
            " all notifications."
        )
        reply_markup = travels_markup(travels)

        return text, reply_markup

    def unsubscribe_all(self, chat_id: int, option: str) -> str:
        if option == "all":
            removed = self.job_manager.remove_subscriptions(chat_id=chat_id)
            text = f"I cancelled {removed} subscriptions."
        else:
            text = (
                "Sorry, I cannot understand that. Did you want to unsubscribe from "
                f"all notifications? For that please use\n<code>/{UNSUBSCRIBE} all</code>"
            )
        return text

    def unsubscribe_one(
        self,
        chat_id: int,
        origin: str,
        destination: str,
        departure_time: datetime.time,
    ) -> str:
        removed = self.job_manager.remove_subscriptions(
            chat_id=chat_id,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
        )
        departure_time_str = (
            str(departure_time.hour).zfill(2)
            + ":"
            + str(departure_time.minute).zfill(2)
        )
        if removed != 0:
            text = (
                f"Subscription from {origin.upper()} to {destination.upper()} "
                f"at {departure_time_str} cancelled!"
            )
        else:
            text = (
                f"I could not find subscriptions to the service between {origin.upper()} "
                f" and {destination.upper()} at {departure_time_str}. See "
                f"<code>/{UNSUBSCRIBE}</code> for more information about your subscriptions."
            )
        return text

    def unsubscribe_departure(self, update: Update, context: CallbackContext) -> None:
        """Remove the job if the user changed their mind."""
        if context.args is None:
            logger.info(f"Got `None` as context.args in {update.message.chat_id}.")
            return

        chat_id: int = update.message.chat_id

        response = "I am sorry I cannot understand that."
        markup = None
        if len(context.args) == 0:
            response, markup = self.unsubscribe_info(chat_id)
        elif len(context.args) == 1:
            response = self.unsubscribe_all(chat_id, context.args[0])
        elif len(context.args) == 3:
            origin, destination, departure_time = context.args
            departure_time = parse_time(departure_time)
            response = self.unsubscribe_one(
                chat_id, origin, destination, departure_time
            )
        update.message.reply_html(response, reply_markup=markup)

    def unsubscribe_button(self, update: Update, context: CallbackContext) -> None:
        """Process button click events from `unsubscribe_info`."""

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query: CallbackQuery = update.callback_query
        query.answer()

        # TODO: this only needs the travel_id from the callback query and chat_id can be
        # retrieved from the context
        if update.effective_chat is None:
            logger.warning(
                f"'unsubscribe_button': 'update.effective_chat' is None. Cannot respond"
                f"to user action. Query data: {query.data}."
            )
            return

        chat_id: int = update.effective_chat.id
        origin, destination, departure_time_str = query.data.split(" ")
        unsubscribe_response = self.unsubscribe_one(
            chat_id,
            origin,
            destination,
            parse_time(departure_time_str),
        )

        response, reply_markup = self.unsubscribe_info(chat_id)
        response = unsubscribe_response + "\n" + response

        query.edit_message_text(
            text=response, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )


def unsubscribe_handler(job_manager: JobManager):
    controller = UnsubscribeController(job_manager=job_manager)
    return (
        CommandHandler(UNSUBSCRIBE, controller.unsubscribe_departure),
        CallbackQueryHandler(controller.unsubscribe_button),
    )
