import logging

from telegram.ext import JobQueue

from rail_bot.bot.service.job_service import create_job_service
from rail_bot.bot.departure_subscription import subscribe_departure

logger = logging.getLogger(__name__)


def recover_jobs(job_queue: JobQueue):
    job_service = create_job_service()
    active_jobs = job_service.get_jobs()

    for job in active_jobs:
        response = subscribe_departure(
            job_queue,
            job.chat_id,
            job.origin,
            job.destination,
            job.departure_time,
        )
        logger.info(response)