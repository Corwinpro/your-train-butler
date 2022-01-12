import os
from datetime import time
from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Time, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.sql.schema import UniqueConstraint

Base = declarative_base()


class Travel(Base):
    __tablename__ = "travel"

    id = Column(Integer, primary_key=True)
    origin = Column(String(3))
    destination = Column(String(3))
    departure_time = Column(Time)

    __table_args__ = (UniqueConstraint("origin", "destination", "departure_time"),)

    def __repr__(self):
        return (
            f"Travel(id={self.id}, "
            f"origin={self.origin!r}, destination={self.destination!r}, "
            f"departure_time={self.departure_time!r})"
        )


class DailySubscription(Base):
    __tablename__ = "daily_subscription"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, index=True)
    travel_id = Column(Integer, ForeignKey("travel.id"), nullable=False)

    __table_args__ = (UniqueConstraint("chat_id", "travel_id"),)

    def __repr__(self):
        return (
            f"DailySubscription(id={self.id}, chat_id={self.chat_id}, "
            f"travel_id={self.travel_id})"
        )


class SubscriptionService:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def shutdown(self):
        self.engine.dispose()

    def _daily_subscription_query(
        self, chat_id: Optional[int] = None, travel_id: Optional[int] = None
    ):
        subscriptions = self.session.query(DailySubscription)

        if chat_id is not None:
            subscriptions = subscriptions.filter_by(chat_id=chat_id)
        if travel_id is not None:
            subscriptions = subscriptions.filter_by(travel_id=travel_id)

        return subscriptions

    def add_subscription(
        self, chat_id: int, origin: str, destination: str, departure_time: time
    ):
        travel = self.add_travel(origin, destination, departure_time)

        subscriptions = DailySubscription(chat_id=chat_id, travel_id=travel.id)
        existing_subscriptions = self._daily_subscription_query(
            chat_id=chat_id, travel_id=travel.id
        ).first()
        if not existing_subscriptions:
            self.session.add(subscriptions)

        self.session.commit()

    def remove_subscriptions(
        self,
        chat_id: int,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        departure_time: Optional[time] = None,
    ) -> int:
        query = self._travel_query(
            origin=origin, destination=destination, departure_time=departure_time
        )
        query = query.with_entities(Travel.id)

        delete_query = self._daily_subscription_query(chat_id=chat_id)
        # Cannot use JOIN here because of SQLAlchemy restrictions. Use in_ instead
        delete_query = delete_query.filter(DailySubscription.travel_id.in_(query))

        deleted = delete_query.delete(synchronize_session=False)
        self.session.commit()

        return deleted

    def get_subscriptions(
        self, chat_id: Optional[int] = None, travel_id: Optional[int] = None
    ) -> List[DailySubscription]:
        subscriptions = self._daily_subscription_query(
            chat_id=chat_id, travel_id=travel_id
        ).all()
        return subscriptions

    def _travel_query(
        self,
        *,
        travel_id: Optional[int] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        departure_time: Optional[time] = None,
        only_active: bool = False,
    ):
        travel_query = self.session.query(Travel)

        for filter_key, filter_value in {
            "id": travel_id,
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
        }.items():
            if filter_value is not None:
                travel_query = travel_query.filter_by(**{filter_key: filter_value})

        if only_active:
            travel_query = travel_query.join(DailySubscription).group_by(Travel.id)

        return travel_query

    def add_travel(self, origin: str, destination: str, departure_time: time) -> Travel:
        travel = self._travel_query(
            origin=origin, destination=destination, departure_time=departure_time
        ).first()

        if not travel:
            travel = Travel(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
            )
            self.session.add(travel)
            self.session.flush()

        return travel

    def get_travels(
        self,
        *,
        travel_id: Optional[int] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        departure_time: Optional[time] = None,
        only_active: bool = False,
    ) -> List[Travel]:
        travels = self._travel_query(
            travel_id=travel_id,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            only_active=only_active,
        )

        travels = travels.all()
        return travels


def create_subscription_service() -> SubscriptionService:
    url = os.environ["DATABASE_URL"]
    url = url.replace("postgres://", "postgresql://")
    service = SubscriptionService(url)
    return service
