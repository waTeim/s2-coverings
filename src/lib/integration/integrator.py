from __future__ import annotations

import glob
import os
from functools import partial
from json import loads
from multiprocessing import Pool
from pathlib import Path

from rdflib import Graph

from ..geo.constrained_s2_region_converer import ConstrainedS2RegionCoverer
from ..geo.geometric_feature import GeometricFeature
from ..geo.geometric_features import GeometricFeatures
from ..rdf.s2_writer import S2Writer


class Integrator:
    """
    Abstraction over the process for integrating s2 cells together with spatial relations.
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
    ):
        """
        Creates a new Integrator

        :param compressed: Whether the triples are compressed or not
        :param geometry_path: Path to the folder where the triples are
        :param output_path: The path where the triples are written to
        :param tolerance: Unknown
        :param min_level: The lowest s2 level to create triples for
        :param max_level: The highest s2 level to create triples for
        """
        self.rdf_format = rdf_format
        if compressed:
            output_folder = Path(
                os.path.join(output_path, f"{geometry_path.stem}_compressed")
            )
        else:
            output_folder = Path(os.path.join(output_path, geometry_path.stem))
        S2Writer.create_output_path(None, output_folder)
        self.spawn_processes(
            geometry_path, output_folder, compressed, tolerance, min_level, max_level
        )

    def spawn_processes(
        self, geometry_path, output_folder, compressed, tolerance, min_level, max_level
    ):
        """ """
        write = partial(
            self.write_all_relations,
            output_folder=output_folder,
            is_compressed=compressed,
            rdf_format=self.rdf_format,
            min_level=min_level,
            max_level=max_level,
        )
        print("Getting features")
        geo_features = GeometricFeatures(geometry_path, tolerance, min_level, max_level)
        print("mapping features")
        with Pool() as pool:
            pool.map(write, [geo_features])

    def write_all_relations(
        self,
        geo_features: [GeometricFeature],
        output_folder: str,
        is_compressed: bool,
        rdf_format: str,
        min_level: int,
        max_level: int,
    ) -> None:
        print("Writing triples")
        graph = Graph()

        for geo_feature in geo_features:
            coverer = ConstrainedS2RegionCoverer(min_level, max_level)
            if not is_compressed:
                if min_level:
                    coverer.set_min_level(min_level)
            else:
                coverer.set_min_level(0)

            for s2_triple in geo_feature.yield_s2_relations(coverer):
                graph.add(s2_triple)

            destination = os.path.join(output_folder, f"test.ttl")
            S2Writer.write(graph, Path(destination), rdf_format)
