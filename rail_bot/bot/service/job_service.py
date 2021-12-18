import os
from typing import List

from sqlalchemy import create_engine, Column, Boolean, Integer, String, Time
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError


DATABASE_URL = os.environ["DATABASE_URL"]


Base = declarative_base()


class DailyJob(Base):
    __tablename__ = "daily_jobs"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, index=True)
    origin = Column(String(3))
    destination = Column(String(3))
    departure_time = Column(Time)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("chat_id", "origin", "destination", "departure_time"),
    )

    def __repr__(self):
        prefix = "(active) " if self.is_active else "(deactivated) "
        return (
            f"{prefix} DailyJob(id={self.id}, chat_id={self.chat_id}, "
            f"origin={self.origin!r}, destination={self.destination!r}, "
            f"departure_time={self.departure_time!r})"
        )


class JobService:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def shutdown(self):
        self.engine.dispose()

    def _query(
        self,
        chat_id=None,
        origin=None,
        destination=None,
        departure_time=None,
        is_active=None,
    ):
        jobs = self.session.query(DailyJob)

        if chat_id is not None:
            jobs = jobs.filter_by(chat_id=chat_id)
        if origin is not None:
            jobs = jobs.filter_by(origin=origin)
        if destination is not None:
            jobs = jobs.filter_by(destination=destination)
        if departure_time is not None:
            jobs = jobs.filter_by(departure_time=departure_time)
        if is_active is not None:
            jobs = jobs.filter_by(is_active=is_active)

        return jobs

    def add_job(self, chat_id, origin, destination, departure_time):
        job = DailyJob(
            chat_id=chat_id,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            is_active=True,
        )
        self.session.add(job)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            self.activate_job(chat_id, origin, destination, departure_time)

    def deactivate_job(self, chat_id, origin, destination, departure_time):
        jobs = self._query(chat_id, origin, destination, departure_time, is_active=True)

        jobs.update({"is_active": False})
        self.session.commit()

    def activate_job(self, chat_id, origin, destination, departure_time):
        jobs = self._query(
            chat_id, origin, destination, departure_time, is_active=False
        )

        jobs.update({"is_active": True})
        self.session.commit()

    def get_jobs(self, chat_id=None) -> List[DailyJob]:
        jobs = self._query(chat_id=chat_id, is_active=True).all()
        return jobs


def create_job_service() -> JobService:
    url = DATABASE_URL.replace("postgres://", "postgresql://")
    job_service = JobService(url)
    return job_service
