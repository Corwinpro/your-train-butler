import datetime
import json
import pkg_resources
import unittest

from rail_bot.rail_api.travel import Travel


EXAMPLE_RESPONSE = pkg_resources.resource_filename(
    "rail_bot.rail_api.tests", "resources/response.json"
)
EXAMPLE_DELAYED_RESPONSE = pkg_resources.resource_filename(
    "rail_bot.rail_api.tests", "resources/response_delayed.json"
)
EXAMPLE_CANCELLED_RESPONSE = pkg_resources.resource_filename(
    "rail_bot.rail_api.tests", "resources/response_cancelled.json"
)
EXAMPLE_CANCELLED_RESPONSE_2 = pkg_resources.resource_filename(
    "rail_bot.rail_api.tests", "resources/response_cancelled_2.json"
)


class TestTravel(unittest.TestCase):
    def test_equal(self):
        travel_1 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure=datetime.time(12, 23),
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival=datetime.time(12, 10),
            estimated_arrival=datetime.time(13, 10),
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 == travel_1)

        travel_2 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure=datetime.time(12, 23),
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival=datetime.time(12, 10),
            estimated_arrival=datetime.time(13, 10),
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 == travel_2)
        self.assertTrue(travel_2 == travel_1)

    def test_assert_not_equal(self):
        travel_1 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure=datetime.time(12, 23),
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival=datetime.time(12, 10),
            estimated_arrival=datetime.time(13, 10),
            estimated_departure="On time",
        )
        travel_2 = Travel(
            origin="cbg",
            destination="kgx",
            scheduled_departure=datetime.time(12, 23),
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival=datetime.time(12, 10),
            estimated_arrival=datetime.time(13, 10),
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 != travel_2)
        self.assertTrue(travel_2 != travel_1)

        travel_3 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure=datetime.time(12, 23),
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival=datetime.time(12, 10),
            estimated_arrival=datetime.time(13, 10),
            estimated_departure=datetime.time(12, 23),
        )

        self.assertTrue(travel_1 != travel_3)
        self.assertTrue(travel_3 != travel_1)

        travel_4 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure=datetime.time(12, 23),
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival=datetime.time(12, 10),
            estimated_arrival=datetime.time(12, 10),
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 != travel_4)
        self.assertTrue(travel_4 != travel_1)

    def test_travel_from_response(self):
        with open(EXAMPLE_RESPONSE) as f:
            response = json.load(f)

        travel = Travel.from_response(response)

        self.assertEqual(travel.origin, "Flowery Field")
        self.assertEqual(travel.destination, "Dinting")
        self.assertEqual(travel.scheduled_departure, datetime.time(19, 46))
        self.assertEqual(travel.estimated_departure, datetime.time(19, 46))
        self.assertEqual(travel.scheduled_arrival, datetime.time(20, 0))
        self.assertEqual(travel.estimated_arrival, datetime.time(20, 0))
        self.assertEqual(travel.service_type, "train")

        self.assertFalse(travel.is_delayed)
        self.assertFalse(travel.is_cancelled)

        self.assertEqual(
            f"{travel!r}", "Train Flowery Field - Dinting\nScheduled at 19:46"
        )

    def test_travel_from_response_delayed(self):
        with open(EXAMPLE_DELAYED_RESPONSE) as f:
            response = json.load(f)

        travel = Travel.from_response(response)

        self.assertEqual(travel.origin, "Flowery Field")
        self.assertEqual(travel.destination, "Dinting")
        self.assertEqual(travel.scheduled_departure, datetime.time(21, 14))
        self.assertEqual(travel.estimated_departure, datetime.time(21, 31))
        self.assertEqual(travel.scheduled_arrival, datetime.time(21, 28))
        self.assertEqual(travel.estimated_arrival, datetime.time(21, 43))
        self.assertEqual(travel.service_type, "train")

        self.assertTrue(travel.is_delayed)
        self.assertFalse(travel.is_cancelled)

        self.assertEqual(
            f"{travel!r}",
            "DELAYED: This train has been delayed by train crew being delayed"
            "\nTrain Flowery Field - Dinting"
            "\nScheduled at 21:14 (expected 21:31)",
        )

    def test_travel_from_response_cancelled(self):
        with open(EXAMPLE_CANCELLED_RESPONSE) as f:
            response = json.load(f)

        travel = Travel.from_response(response)

        self.assertEqual(travel.origin, "London Kings Cross")
        self.assertEqual(travel.destination, "Sunderland")
        self.assertEqual(travel.scheduled_departure, datetime.time(8, 27))
        self.assertEqual(travel.estimated_departure, "Cancelled")
        self.assertEqual(travel.scheduled_arrival, datetime.time(12, 4))
        self.assertEqual(travel.estimated_arrival, datetime.time(12, 4))
        self.assertEqual(travel.service_type, "train")

        self.assertTrue(travel.is_delayed)
        self.assertTrue(travel.is_cancelled)

        self.assertEqual(
            f"{travel!r}",
            "CANCELLED: This train has been cancelled because of more trains "
            "than usual needing repairs at the same time\n"
            "Train London Kings Cross - Sunderland",
        )

    def test_travel_from_response_cancelled_2(self):
        with open(EXAMPLE_CANCELLED_RESPONSE_2) as f:
            response = json.load(f)

        travel = Travel.from_response(response)

        self.assertEqual(travel.origin, "Earlswood (Surrey)")
        self.assertEqual(travel.destination, "Horley")
        self.assertEqual(travel.scheduled_departure, datetime.time(8, 57))
        self.assertEqual(travel.estimated_departure, "Cancelled")
        self.assertEqual(travel.scheduled_arrival, datetime.time(9, 4))
        self.assertEqual(travel.estimated_arrival, datetime.time(9, 4))
        self.assertEqual(travel.service_type, "train")

        self.assertTrue(travel.is_delayed)
        self.assertTrue(travel.is_cancelled)

        print(f"{travel!r}")
        self.assertEqual(
            f"{travel!r}",
            "CANCELLED: This train has been cancelled because of flooding\n"
            "Train Earlswood (Surrey) - Horley",
        )


if __name__ == "__main__":
    unittest.main()
