import datetime
import logging
from typing import Optional

from telegram.ext import JobQueue
from telegram.ext.callbackcontext import CallbackContext

from rail_bot.bot.service.subscription_service import SubscriptionService
from rail_bot.bot.utils import shift_time
from rail_bot.rail_api.api import next_departure_status
from rail_bot.rail_api.travel import Travel

logger = logging.getLogger(__name__)


def subscribe_travel_job_name(
    origin: str, destination: str, departure_time: datetime.time
) -> str:
    return f"{origin.lower()}-{destination.lower()}-{departure_time}"


class JobManager:
    def __init__(self, job_queue: JobQueue, service: SubscriptionService):
        self.job_queue = job_queue
        self.service = service

    def remove_subscriptions(
        self,
        chat_id: int,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        departure_time: Optional[datetime.time] = None,
    ) -> int:
        removed = self.service.remove_subscriptions(
            chat_id=chat_id,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
        )

        # TODO: this should remove jobs without subscribers
        # active_travels = self.service.get_travels(
        #     origin, destination, departure_time, only_active=True
        # )
        # if len(active_travels) == 0:
        #     job_name = subscribe_travel_job_name(origin, destination, departure_time)
        #     job_removed = self.remove_jobs_by_prefix(job_name)

        return removed

    def remove_jobs_by_prefix(self, prefix: str) -> int:
        """Remove jobs with given name prefix.
        Returns the number of job that were removed.
        """
        current_jobs = [
            job for job in self.job_queue.jobs() if job.name.startswith(prefix)
        ]

        for job in current_jobs:
            job.schedule_removal()

        return len(current_jobs)

    def recover_travel_jobs(self):
        travels = self.service.get_travels(only_active=True)
        travels_repr = "\n".join([f"{travel!r}" for travel in travels])
        logger.info(
            f"Found {len(travels)} active travels that will be recovered. "
            f"{travels_repr}"
        )

        for travel in travels:
            self._submit_travel_job(
                travel.origin, travel.destination, travel.departure_time
            )

    def add_subscription(
        self,
        chat_id: int,
        origin: str,
        destination: str,
        departure_time: datetime.time,
    ) -> str:
        active_travel = self.service.get_travels(
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            only_active=True,
        )
        self.service.add_subscription(
            chat_id=chat_id,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
        )

        if len(active_travel) == 0:
            self._submit_travel_job(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
            )

        response = (
            f"Subscribed to updates between {origin.upper()} and {destination.upper()}"
            f" at {departure_time}."
        )
        return response

    def _submit_travel_job(
        self,
        origin: str,
        destination: str,
        departure_time: datetime.time,
    ) -> None:
        datetime_now = datetime.datetime.now()
        job_name = subscribe_travel_job_name(origin, destination, departure_time)

        # The scheduled departure check is initiated some time before the departure
        first_check_time = shift_time(departure_time, delta_hour=-1, delta_minute=0)

        # only on weekdays
        days = tuple(range(7))

        context = (origin, destination, departure_time, None)
        self.job_queue.run_daily(
            self.get_travel_status,
            time=first_check_time,
            days=days,
            context=context,
            name=job_name,
        )
        logger.info(
            f"Started daily job {job_name} between {origin.upper()} and "
            f"{destination.upper()} at {departure_time}."
        )

        if first_check_time < datetime_now.time() < departure_time:
            name = job_name + f"-{datetime_now}"
            context = (origin, destination, departure_time, None)
            self.job_queue.run_once(
                callback=self.get_travel_status,
                when=1,
                context=context,
                name=name,
            )
            logger.info(f"Started run once job {name} with {context!r}")

    def get_travel_status(self, context: CallbackContext):
        """TODO: this is super awkward it depends on a ``CallbackContext``."""
        if context.job is None:
            logger.info("Got `None` as context.job in `get_travel_status`.")
            return

        logger.info(f"get_travel_status: {context.job.context}")

        origin, destination, departure_time, travel_obj = context.job.context

        response, rerun_in, current_travel_obj = _get_travel_status(
            origin, destination, departure_time, travel_obj
        )
        if rerun_in is not None:
            current_time = datetime.datetime.now()
            job_name = (
                subscribe_travel_job_name(origin, destination, departure_time)
                + f"-{current_time}"
            )
            _context = (origin, destination, departure_time, current_travel_obj)
            self.job_queue.run_once(
                self.get_travel_status,
                when=rerun_in,
                context=_context,
                name=job_name,
            )
            logger.info(f"Started run once job {job_name} with {_context!r}")

        if response is not None:
            (travel,) = self.service.get_travels(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                only_active=True,
            )
            subscribers = self.service.get_subscriptions(travel_id=travel.id)
            for subscriber in subscribers:
                context.bot.send_message(subscriber.chat_id, text=response)


def _get_travel_status(
    origin: str, destination: str, time: datetime.time, travel_obj: Travel
):
    response: Optional[str] = None
    rerun_in: Optional[int] = None

    current_time = datetime.datetime.now()
    if current_time > datetime.datetime.combine(datetime.date.today(), time):
        # Already too late
        return None, None, None

    current_travel_obj = next_departure_status(origin, destination)

    if current_travel_obj is None:
        response = "❗ It seems that your travel has been cancelled. ❗\n"
        response += "I am sorry I could not find any additional information."
    else:
        if current_travel_obj.is_delayed or current_travel_obj.is_cancelled:
            if current_travel_obj != travel_obj:
                response = f"{current_travel_obj!r}"

            rerun_in = 2 * 60  # seconds
        else:
            rerun_in = 10 * 60  # seconds

    return response, rerun_in, current_travel_obj
