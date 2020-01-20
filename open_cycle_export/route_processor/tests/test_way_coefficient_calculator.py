import unittest

from open_cycle_export.route_processor.way_coefficient_calculator import (
    create_way_coefficient_calculator,
)


class TestRouteNavigation(unittest.TestCase):
    def setUp(self):
        self.calculate_way_coefficient = create_way_coefficient_calculator(
            ["cycle_only", "cycle_permitted", "passible_road", "impassible"]
        )

    def test_oneway_forward_navigable(self):
        properties = {"oneway": "yes"}
        result = self.calculate_way_coefficient(properties, "bicycle", "forward")
        self.assertEqual(result, "passible_road")

    def test_oneway_reverse_not_navigable(self):
        properties = {"oneway": "yes"}
        result = self.calculate_way_coefficient(properties, "bicycle", "reverse")
        self.assertEqual(result, "impassible")

    def test_oneway_reverse_bicycle_navigable(self):
        properties = {"oneway": "yes", "oneway:bicycle": "no"}
        result = self.calculate_way_coefficient(properties, "bicycle", "reverse")
        self.assertEqual(result, "passible_road")

    def test_bicycle_designated(self):
        properties = {"bicycle": "designated"}
        result = self.calculate_way_coefficient(properties, "bicycle")
        self.assertEqual(result, "cycle_only")

    def test_bicycle_designated_oneway(self):
        properties = {"bicycle": "designated", "oneway": "yes"}
        result = self.calculate_way_coefficient(properties, "bicycle", "reverse")
        self.assertEqual(result, "impassible")

    def test_bicycle_permitted(self):
        properties = {"bicycle": "permitted"}
        result = self.calculate_way_coefficient(properties, "bicycle")
        self.assertEqual(result, "cycle_permitted")

    def test_bicycle_specified(self):
        properties = {"bicycle": "yes"}
        result = self.calculate_way_coefficient(properties, "bicycle")
        self.assertEqual(result, "cycle_only")
