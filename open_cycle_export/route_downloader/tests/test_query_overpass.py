import unittest

from open_cycle_export.route_downloader.query_overpass import minify_query


class TestQueryOverpass(unittest.TestCase):
    def test_minify_simple_query(self):
        minified_query = minify_query("node(1, 2, 3, 4)")
        self.assertEqual(minified_query, "node(1,2,3,4)")

    def test_minify_with_strings(self):
        query = """area["name"="United Kingdom"]"""
        minified_query = minify_query(query)
        self.assertEqual(query, minified_query)

    def test_complex_minify_with_strings(self):
        minified_query = minify_query(
            """
            area["name"="United Kingdom"]->.boundaryarea;
            (
            relation
                (area.boundaryarea)
                ["route"="bicycle"]
                ["network"="ncn"]
                ["ref"="22"];
            way(r);
            );
        """
        )
        expected_query = """area["name"="United Kingdom"]->.boundaryarea;(relation(area.boundaryarea)["route"="bicycle"]["network"="ncn"]["ref"="22"];way(r););"""
        self.assertEqual(minified_query, expected_query)
