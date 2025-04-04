from __future__ import annotations

import os
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from rdflib import Graph

from ..geo.constrained_s2_region_converer import ConstrainedS2RegionCoverer
from ..geo.geometric_features import GeometricFeatures
from ..rdf.kwg_ont import file_extensions
from ..rdf.s2_writer import S2Writer


class Integrator:
    """Abstraction over the process for integrating s2 cells together with spatial relations.

    This class is responsible for processing geometric features into RDF triples,
    and writing them out using the S2 hierarchy.
    """

    def __init__(
        self,
        compressed: bool,
        geometry_path: Path,
        output_path: Path,
        tolerance: float,
        min_level: int,
        max_level: int,
        rdf_format: str,
        pool_size: int = 4,
    ):
        """Create a new Integrator.

        Args:
            compressed (bool): Whether the triples are compressed or not.
            geometry_path (Path): Path to the folder where the triples are.
            output_path (Path): The path where the triples are written to.
            tolerance (float): Tolerance used during spatial operations.
            min_level (int): The lowest s2 level to create triples for.
            max_level (int): The highest s2 level to create triples for.
            rdf_format (str): The RDF serialization format.
            pool_size (int, optional): Number of processes to use in the pool. Defaults to 4.
        """
        self.rdf_format = rdf_format
        if compressed:
            output_folder = Path(os.path.join(output_path, f"level_{min_level}_compressed"))
        else:
            output_folder = Path(os.path.join(output_path, f"level_{min_level}"))
        S2Writer.create_output_path(None, output_folder)
        self.spawn_processes(geometry_path, output_folder, compressed, tolerance, min_level, max_level, pool_size)

    def spawn_processes(self, geometry_path, output_folder, compressed, tolerance, min_level, max_level, pool_size):
        """Spawn processes using a Pool with an explicitly provided pool size.

        Args:
            geometry_path (Path): Path to the folder containing geometry data.
            output_folder (Path): Folder where output files will be written.
            compressed (bool): Flag indicating whether compression is used.
            tolerance (float): Tolerance used in spatial operations.
            min_level (int): Minimum s2 level for processing.
            max_level (int): Maximum s2 level for processing.
            pool_size (int): Number of processes to use in the pool.
        """
        write = partial(
            self.write_all_relations,
            output_folder=output_folder,
            is_compressed=compressed,
            rdf_format=self.rdf_format,
            min_level=min_level,
            max_level=max_level,
        )
        geo_features = GeometricFeatures(geometry_path, tolerance, min_level, max_level)
        with Pool(processes=pool_size) as pool:
            pool.map(write, [geo_features])

    def write_all_relations(
        self,
        geo_features: GeometricFeatures,
        output_folder: str,
        is_compressed: bool,
        rdf_format: str,
        min_level: int,
        max_level: int,
    ) -> None:
        """Write all RDF relations generated from the given geometric features.

        Iterates through each geometric feature, converts it into RDF triples
        using a constrained S2 region coverer, and writes the output to the designated folder.

        Args:
            geo_features (GeometricFeatures): The geometric features to process.
            output_folder (str): The folder to write output files.
            is_compressed (bool): Flag indicating if compression is applied.
            rdf_format (str): The RDF serialization format.
            min_level (int): The minimum s2 level to use.
            max_level (int): The maximum s2 level to use.

        Returns:
            None
        """
        graph = Graph()
        filename = ""
        for geo_feature in geo_features:
            filename = geo_feature.iri
            coverer = ConstrainedS2RegionCoverer(min_level, max_level)
            if not is_compressed:
                if min_level:
                    coverer.set_min_level(min_level)
            else:
                coverer.set_min_level(0)

            for s2_triple in geo_feature.yield_s2_relations(coverer):
                graph.add(s2_triple)
            filename = filename.split("/")[-1] + file_extensions[rdf_format]
        destination = os.path.join(output_folder, filename)
        print(destination)
        S2Writer.write(graph, Path(destination), rdf_format)
