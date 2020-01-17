import unittest

from shapely.geometry import LineString

from open_cycle_export.shapely_utilities.line_string_tools import reverse_line_string


class TestReverseLineString(unittest.TestCase):
    """Test that a line string direction can be reversed"""

    def test_reverse_line_string_coords(self):
        line_string = LineString([(0, 0), (1, 1)])
        reversed_line_string = reverse_line_string(line_string)
        self.assertListEqual(list(reversed_line_string.coords), [(1, 1), (0, 0)])
