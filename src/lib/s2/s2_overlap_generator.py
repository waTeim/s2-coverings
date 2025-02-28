import os
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict, Generator, List

from rdflib import Graph
from s2geometry import S2Cell, S2CellId, S2RegionCoverer
from shapely import union_all
from shapely.wkt import loads

from ..geo.geometric_feature import GeometricFeature
from ..geo.geometry_parser import GeometryParser
from ..rdf.kwg_ont import file_extensions
from ..rdf.s2_writer import S2Writer
from ..s2.s2_rdf_generator import S2RDFGenerator


class S2OverlapGenerator:
    """
    Generates S2Cells that overlap with a geometry
    """

    def __init__(
        self,
        geometry_path: Path,
        rdf_format: str,
        tolerance: float,
        min_level,
        max_level,
        output_folder,
        batch_size: int,
    ):
        """
        Create a new S2OverlapGenerator.

        :param geometry_path: The path to the custom geometry folder
        :param rdf_format: The format of the RDf
        :param tolerance: The tolerance to use
        :param min_level: The minimum level to cover
        :param max_level: The maximum level to cover
        :param output_folder: The folder to write the RDF
        :param batch_size: The number of geometries to write to a single file
        """
        self.tolerance = tolerance
        self.min_level = min_level
        self.max_level = max_level
        self.rdf_format = rdf_format
        self.batch_size = batch_size
        self.output_folder = Path(output_folder)
        self.geometry_path = Path(geometry_path)

        S2Writer.create_output_path(max_level, output_folder)
        # ResultSets can't be pickled, so we're forced to
        # load everything into memory here
        batch_results = self.batch_result_sets()
        with Pool() as pool:
            pool.map(self.write_to_rdf, batch_results)

    def batch_result_sets(self) -> Generator[List[Dict[str, str]], None, None]:
        """
        Takes a batch of sparql results and batches them
        """
        result_set = []
        for geo_result in GeometryParser.parse(self.geometry_path):
            result_set.append(
                {"wkt": geo_result["wkt"], "feature_iri": geo_result["feature_iri"]}
            )
            if len(result_set) == self.batch_size:
                yield result_set
                result_set = []
        if not len(result_set):
            return
        yield result_set

    def write_to_rdf(
        self, result_batch: Generator[List[Dict[str, str]], Any, None]
    ) -> None:
        """
        Writes an S2Cell to RDF

        :param result_batch: A batch of query results in the form [{'wkt': , 'feature_iri': }
        """
        graph = Graph()

        file_prepend = ""
        for single_result in self.generate_cell_batches(result_batch):
            for cell_id in single_result:
                single_cell_id = S2CellId(cell_id)
                file_prepend = single_cell_id.id()
                level = single_cell_id.level()
                parent = None
                if level > 0:
                    parent = single_cell_id.parent()
                rdf_generator = S2RDFGenerator(single_cell_id.id(), parent.id(), "ttl")
                graph += rdf_generator.graph
        file_name = str(file_prepend) + file_extensions[self.rdf_format]
        destination = os.path.join(
            self.output_folder, f"level_{self.max_level}", file_name
        )
        S2Writer.write(graph, Path(destination), "ttl")

    def get_ids(self, current_batch) -> List[int]:
        """
        Given a batch of geometries, combine them all and
        find the s2 cells that cover it.

        :param current_batch: The batch of geometries being combined
        """
        batch = list(current_batch)
        geometry = union_all(batch, grid_size=1e-7)
        coverer = S2RegionCoverer()
        coverer.set_max_level(self.max_level)
        coverer.set_min_level(self.min_level)
        feature = GeometricFeature(
            geometry, None, self.tolerance, self.min_level, self.max_level
        )
        return [cell_id.id() for cell_id in feature.covering(coverer)]

    def generate_cell_batches(
        self, features: Generator[List[Dict[str, str]], Any, None]
    ) -> Generator[list[int] | list[list[int]], None, None]:
        """
        Given a set of features, generate the identifiers of the S2 cells that overlap it.
        This works by first loading the WKT RDF result into a shapely geometry. Then,
        the s2 cells that overlap the batch are computed

        :param features: The set of geometries, as RDF results
        :return: Batches of s2 cells, limited by the batch size
        """
        geo_batch = []
        for feature in features:
            if len(geo_batch) == self.batch_size:
                yield self.get_ids(geo_batch)
                geo_batch = []
            geo_batch.append(loads(feature["wkt"]))
        if not len(geo_batch):
            return
        yield self.get_ids(geo_batch)
