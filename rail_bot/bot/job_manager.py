from telegram.ext import JobQueue


def remove_job_by_prefix(name: str, job_queue: JobQueue) -> bool:
    """ Remove job with given name prefix. Returns whether job was removed."""
    current_jobs = job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True
