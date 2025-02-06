import os
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import List

from rdflib import Graph
from s2geometry import S2Cell, S2CellId, S2RegionCoverer
from shapely import union_all
from shapely.wkt import loads

from ..geo.geometric_feature import GeometricFeature
from ..geo.geometry_parser import GeometryParser
from ..rdf.s2_writer import S2Writer
from ..s2.s2_rdf_generator import S2RDFGenerator
from ..rdf.kwg_ont import file_extensions

class S2OverlapGenerator:
    """
    Generates S2Cells that overlap with a geometry
    """

    def write_to_rdf(self, cell_id_int: List[int], output_path: str) -> None:
        """
        Writes an S2Cell to RDF
        :param cell_id_int: The s2 cell ID
        :param output_path: The folder to write the RDF
        """
        graph = Graph()
        for single_cell_id in cell_id_int:
            single_cell_id = S2CellId(single_cell_id)
            level = single_cell_id.level()
            parent = None
            if level > 0:
                parent = single_cell_id.parent()
            rdf_generator = S2RDFGenerator(single_cell_id.id(), parent.id(), "ttl")
            graph += rdf_generator.graph
        file_name = str(cell_id_int[0]) + file_extensions[self.rdf_format]
        destination = os.path.join(output_path, file_name)

        S2Writer.write(graph, Path(destination), "ttl")

    def get_ids(self, current_batch) -> List[int]:
        """
        Given a batch of geometries, combine them all and
        find the s2 cells that cover it.

        :param current_batch: The batch of geometries being combined
        """
        geometry = union_all(current_batch, grid_size=1e-7)
        coverer = S2RegionCoverer()
        coverer.set_max_level(self.max_level)
        coverer.set_min_level(self.min_level)
        feature = GeometricFeature(
            geometry, None, self.tolerance, self.min_level, self.max_level
        )
        return [cell_id.id() for cell_id in feature.covering(coverer)]

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
        features = list(GeometryParser.parse(geometry_path))

        current_batch = []
        cell_batches = []
        for feature in features:
            if len(current_batch) == batch_size:
                cell_batches.append(self.get_ids(current_batch))
                current_batch = []
            current_batch.append(loads(feature["wkt"]))
        cell_batches.append(self.get_ids(current_batch))

        level = max_level
        output_path = os.path.join(output_folder, str(level))
        os.makedirs(output_path, exist_ok=True)
        write = partial(self.write_to_rdf, output_path=output_path)
        with Pool() as pool:
            pool.map(write, cell_batches)
