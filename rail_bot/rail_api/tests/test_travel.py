import unittest

from rail_bot.rail_api.travel import Travel


class TestTravel(unittest.TestCase):
    def test_equal(self):
        travel_1 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure="12:23",
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival="12:10",
            estimated_arrival=None,
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 == travel_1)

        travel_2 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure="12:23",
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival="12:10",
            estimated_arrival=None,
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 == travel_2)
        self.assertTrue(travel_2 == travel_1)

    def test_assert_not_equal(self):
        travel_1 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure="12:23",
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival="12:10",
            estimated_arrival=None,
            estimated_departure="On time",
        )
        travel_2 = Travel(
            origin="cbg",
            destination="kgx",
            scheduled_departure="12:23",
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival="12:10",
            estimated_arrival=None,
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 != travel_2)
        self.assertTrue(travel_2 != travel_1)

        travel_3 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure="12:23",
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival="12:10",
            estimated_arrival=None,
            estimated_departure="12:23",
        )

        self.assertTrue(travel_1 != travel_3)
        self.assertTrue(travel_3 != travel_1)

        travel_4 = Travel(
            origin="kgx",
            destination="cbg",
            scheduled_departure="12:23",
            service_type="train",
            delay_info=None,
            cancel_info=None,
            scheduled_arrival="12:10",
            estimated_arrival="12:10",
            estimated_departure="On time",
        )

        self.assertTrue(travel_1 != travel_4)
        self.assertTrue(travel_4 != travel_1)


if __name__ == "__main__":
    unittest.main()
