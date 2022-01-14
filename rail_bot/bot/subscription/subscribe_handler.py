import datetime
import logging

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from rail_bot.bot.job_manager import JobManager
from rail_bot.bot.subscription.common import SUBSCRIBE
from rail_bot.bot.utils import parse_time

logger = logging.getLogger(__name__)


class SubscribeController:
    def __init__(self, job_manager: JobManager) -> None:
        self.job_manager = job_manager

    def _subscribe_departure(
        self,
        chat_id: int,
        origin: str,
        destination: str,
        departure_time: datetime.time,
    ) -> str:
        response = self.job_manager.add_subscription(
            chat_id, origin, destination, departure_time
        )
        return response

    def subscribe_departure(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id

        if context.args is None:
            logger.info(
                f"Got `None` as context.args in `subscribe_departure` with {chat_id}."
            )
            return

        try:
            origin, destination, departure_time = context.args
        except ValueError:
            update.message.reply_text(
                "Subscribe to service updates by specifying "
                "\n-The origin of your travel (e.g., 'kgx'),"
                "\n-The destination of your travel (e.g., 'cbg'),"
                "\n-Departure time (e.g., '12:23')."
            )
            return

        try:
            departure_time = parse_time(departure_time)
        except Exception as e:
            update.message.reply_text(f"{e!r}")
            return

        response = self._subscribe_departure(
            chat_id, origin, destination, departure_time
        )
        update.message.reply_text(response)


def subscribe_handler(job_manager: JobManager):
    controller = SubscribeController(job_manager=job_manager)
    return CommandHandler(SUBSCRIBE, controller.subscribe_departure)
