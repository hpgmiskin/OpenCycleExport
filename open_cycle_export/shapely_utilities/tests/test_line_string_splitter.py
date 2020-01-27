import unittest

import sys

import shapely.geometry
from shapely.geometry import LineString

from open_cycle_export.test_data.test_data_loader import load_test_data
from open_cycle_export.shapely_utilities.line_string_splitter import (
    split_line_by_intersecting_lines,
)


class TestLineStringSplitter(unittest.TestCase):
    """Test the splitting of line strings by intersecting lines and points"""

    @classmethod
    def setUpClass(self):
        self.recursionlimit = sys.getrecursionlimit()
        sys.setrecursionlimit(64)

    def test_split_simple_line_string(self):
        line = LineString([(0, 0), (1, 1), (2, 2), (3, 3)])
        intersecting_lines = [
            LineString([(1, 1), (2, 0)]),
            LineString([(2, 2), (1, 3)]),
        ]
        line_segments = split_line_by_intersecting_lines(line, intersecting_lines)
        self.assertEqual(len(line_segments), 3)
        self.assertListEqual(list(line_segments[0].coords), [(0, 0), (1, 1)])
        self.assertListEqual(list(line_segments[1].coords), [(1, 1), (2, 2)])
        self.assertListEqual(list(line_segments[2].coords), [(2, 2), (3, 3)])

    def test_real_example_split_linestring(self):
        real_example_data = load_test_data("test_line_string_splitter_data.json")
        line = shapely.geometry.shape(real_example_data["line"])
        intersecting_lines = real_example_data["intersecting_lines"]
        intersecting_lines = list(map(shapely.geometry.shape, intersecting_lines))
        line_segments = split_line_by_intersecting_lines(line, intersecting_lines)
        self.assertEqual(len(line_segments), 2)

    @classmethod
    def tearDownClass(self):
        sys.setrecursionlimit(self.recursionlimit)
