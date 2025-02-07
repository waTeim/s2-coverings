import unittest
from pathlib import Path
from unittest.mock import patch

import rdflib
from shapely.wkt import loads

from src.lib.s2.s2_overlap_generator import S2OverlapGenerator


def generate_geometry():
    """
    Generates two level 1 s2 cell records
    """
    sparql_results = [
        {
            "feature_iri": rdflib.term.URIRef(
                "http://stko-kwg.geog.ucsb.edu/lod/resource/geometry.polygon.s2.level1.10088063165309911040"
            ),
            "wkt": rdflib.term.Literal(
                "POLYGON ((-90 45, -90 0, -45 0, -45 35.264389682754654, -90 45))",
            ),
        },
        {
            "feature_iri": rdflib.term.URIRef(
                "http://stko-kwg.geog.ucsb.edu/lod/resource/geometry.polygon.s2.level1.10664523917613334528"
            ),
            "wkt": rdflib.term.Literal(
                "POLYGON ((-90 0, -90 -45, -45 -35.264389682754654, -45 0, -90 0))",
            ),
        },
    ]
    for geom in sparql_results:
        yield geom


class OverlapGeneratorTests(unittest.TestCase):
    @patch("src.lib.s2.s2_overlap_generator.S2OverlapGenerator.batch_result_sets")
    @patch("src.lib.rdf.s2_writer.S2Writer.create_output_path")
    @patch("multiprocessing.pool.Pool.map")
    def setUp(self, map_mock, writer_mock, result_sets_mock):
        """This method will run before each test."""
        geometry_path = Path("not_real/")
        rdf_format = "ttl"
        tolerance = 0.002
        min_level = 2
        max_level = 2
        output_folder = Path("not_real/")
        batch_size = 10
        self.overlap_generator = S2OverlapGenerator(
            geometry_path,
            rdf_format,
            tolerance,
            min_level,
            max_level,
            output_folder,
            batch_size,
        )

    @patch("src.lib.geo.geometry_parser.GeometryParser.parse")
    def test_batch_result_sets(self, parser_mock):
        """
        Given SPARQL results, check that the batches are correct
        """

        parser_mock.return_value = generate_geometry()
        self.overlap_generator.batch_size = 1
        batch = list(self.overlap_generator.batch_result_sets())

        # Because the batch size is 1, we should get 2 results back
        assert len(batch) == 2

    def test_generate_cell_batches_small_batch(self):
        """
        Test that small batches (below the max batch limit)
        are still returned
        """
        self.overlap_generator.batch_size = 10
        res = self.overlap_generator.generate_cell_batches(generate_geometry())
        res = list(res)
        assert len(res) == 1

    def test_generate_cell_batches_large_batch(self):
        """
        Test that large batches (above the max batch limit)
        are still returned
        """
        self.overlap_generator.batch_size = 10
        res = self.overlap_generator.generate_cell_batches(generate_geometry())
        res = list(res)
        assert len(res) == 1

    def test_write_to_rdf_small_batch(
        self,
    ):
        """
        Tests that small batch sizes properly chunk
        the results
        """
        self.overlap_generator.batch_size = 1
        res = self.overlap_generator.generate_cell_batches(generate_geometry())
        res = list(res)
        assert len(res) == 2

    def test_get_ids(self):
        """
        Tests that ids are returned for coverings. The test coverings
        in the `generate` function have 22 cells that cover.
        """
        self.overlap_generator.batch_size = 10

        geo_batch = []
        for feature in generate_geometry():
            geo_batch.append(loads(feature["wkt"]))

        res = self.overlap_generator.get_ids(geo_batch)
        res = list(res)
        assert len(res) == 22
