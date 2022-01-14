import datetime
import os
import unittest

from rail_bot.bot.service.subscription_service import Base, SubscriptionService

TEST_DB_USER = "postgres"
TEST_DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "mysecretpassword")
TEST_DB_HOST = "localhost"
TEST_DB_PORT = 5432
TEST_DB_URL = (
    f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}"
)
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "test_db")


class TestSubscriptionService(unittest.TestCase):
    def setUp(self) -> None:
        url = f"{TEST_DB_URL}/{TEST_DB_NAME}"
        self.service = SubscriptionService(database_url=url)

    def tearDown(self) -> None:
        self.service.session.close()
        Base.metadata.drop_all(self.service.engine)

    def test_add_get_subscription(self):
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )

        (travel,) = self.service.get_travels()
        self.assertEqual(travel.origin, "aaa")
        self.assertEqual(travel.destination, "bbb")
        self.assertEqual(travel.departure_time, datetime.time(11, 12, 28))

        (job,) = self.service.get_subscriptions()
        self.assertEqual(job.chat_id, 1)
        self.assertEqual(job.travel_id, travel.id)

        # Same job added
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )

        (travel,) = self.service.get_travels()
        self.assertEqual(travel.origin, "aaa")
        self.assertEqual(travel.destination, "bbb")
        self.assertEqual(travel.departure_time, datetime.time(11, 12, 28))

        (job,) = self.service.get_subscriptions()
        self.assertEqual(job.chat_id, 1)
        self.assertEqual(job.travel_id, travel.id)

    def test_add_get_subscriptions(self):
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )
        self.service.add_subscription(
            chat_id=2,
            origin="aaa",
            destination="ccc",
            departure_time=datetime.time(13, 32, 38),
        )

        travels = self.service.get_travels()
        self.assertEqual(len(travels), 2)

        first_travel, second_travel = sorted(
            travels, key=lambda travel: travel.departure_time
        )

        self.assertEqual(first_travel.origin, "aaa")
        self.assertEqual(first_travel.destination, "bbb")
        self.assertEqual(first_travel.departure_time, datetime.time(11, 12, 28))

        self.assertEqual(second_travel.origin, "aaa")
        self.assertEqual(second_travel.destination, "ccc")
        self.assertEqual(second_travel.departure_time, datetime.time(13, 32, 38))

        jobs = self.service.get_subscriptions()

        first_job, second_job = sorted(jobs, key=lambda job: job.chat_id)
        self.assertEqual(first_job.chat_id, 1)
        self.assertEqual(first_job.travel_id, first_travel.id)

        self.assertEqual(second_job.chat_id, 2)
        self.assertEqual(second_job.travel_id, second_travel.id)

    def test_remove_subscriptions_by_chat_id(self):
        # Given
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )

        # When
        self.service.remove_subscriptions(chat_id=2)
        (job,) = self.service.get_subscriptions()

        # Then
        self.assertEqual(job.chat_id, 1)

        # When
        self.service.remove_subscriptions(chat_id=1)
        jobs = self.service.get_subscriptions()

        # Then
        self.assertEqual(len(jobs), 0)

        # When
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )
        self.service.add_subscription(
            chat_id=1,
            origin="ccc",
            destination="ddd",
            departure_time=datetime.time(11, 12, 28),
        )
        self.service.remove_subscriptions(chat_id=1)
        jobs = self.service.get_subscriptions()

        # Then
        self.assertEqual(len(jobs), 0)

    def test_remove_subscriptions_by_travel_data(self):
        # Given
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )
        self.service.add_subscription(
            chat_id=1,
            origin="ccc",
            destination="ddd",
            departure_time=datetime.time(22, 24, 56),
        )

        # When
        self.service.remove_subscriptions(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )
        (job,) = self.service.get_subscriptions()

        # Then
        (travel,) = self.service.get_travels(origin="ccc")
        self.assertEqual(job.travel_id, travel.id)

    def test_get_travels_active(self):
        # Given
        self.service.add_subscription(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )
        self.service.add_subscription(
            chat_id=1,
            origin="ccc",
            destination="ddd",
            departure_time=datetime.time(22, 24, 56),
        )
        self.service.add_subscription(
            chat_id=2,
            origin="ccc",
            destination="ddd",
            departure_time=datetime.time(22, 24, 56),
        )

        # When
        travels = self.service.get_travels(only_active=True)

        # Then
        self.assertEqual(len(travels), 2)

        # When
        self.service.remove_subscriptions(
            chat_id=1,
            origin="aaa",
            destination="bbb",
            departure_time=datetime.time(11, 12, 28),
        )

        # Then
        travels = self.service.get_travels(only_active=True)
        self.assertEqual(len(travels), 1)

        # When
        self.service.remove_subscriptions(
            chat_id=2,
            origin="ccc",
            destination="ddd",
            departure_time=datetime.time(22, 24, 56),
        )

        # Then
        travels = self.service.get_travels(only_active=True)
        self.assertEqual(len(travels), 1)

        # When
        self.service.remove_subscriptions(
            chat_id=1,
            origin="ccc",
            destination="ddd",
            departure_time=datetime.time(22, 24, 56),
        )

        # Then
        travels = self.service.get_travels(only_active=True)
        self.assertEqual(len(travels), 0)


if __name__ == "__main__":
    unittest.main()
