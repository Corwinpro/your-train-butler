from telegram.ext import JobQueue


def remove_jobs_by_prefix(prefix: str, job_queue: JobQueue) -> bool:
    """ Remove job with given name prefix. Returns whether job was removed."""
    current_jobs = [job for job in job_queue.jobs() if job.name.startswith(prefix)]
    if not current_jobs:
        return False

    for job in current_jobs:
        job.schedule_removal()
    return True
