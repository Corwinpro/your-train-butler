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


if __name__ == "__main__":
    unittest.main()
