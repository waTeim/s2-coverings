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
    """
    Extended version of Integrator that flushes RDF triples in batches.
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
        flush_threshold: int = 10000,  # Number of triples to accumulate before flushing
    ):
        """
        Create a new ExtendedIntegrator.

        Args:
            compressed (bool): Whether the triples are compressed or not.
            geometry_path (Path): Path to the folder where the geometric features are located.
            output_path (Path): The directory where the RDF output files will be written.
            tolerance (float): Tolerance used during spatial operations.
            min_level (int): The lowest S2 level to create triples for.
            max_level (int): The highest S2 level to create triples for.
            rdf_format (str): The RDF serialization format (e.g., 'turtle').
            pool_size (int, optional): Number of processes to use in the pool. Defaults to 4.
            flush_threshold (int, optional): Number of triples to accumulate before flushing. Defaults to 10000.
        """
        self.rdf_format = rdf_format
        self.flush_threshold = flush_threshold
        if compressed:
            output_folder = Path(os.path.join(output_path, f"level_{min_level}_compressed"))
        else:
            output_folder = Path(os.path.join(output_path, f"level_{min_level}"))
        S2Writer.create_output_path(None, output_folder)
        self.spawn_processes(geometry_path, output_folder, compressed, tolerance, min_level, max_level, pool_size)

    def spawn_processes(self, geometry_path, output_folder, compressed, tolerance, min_level, max_level, pool_size):
        """
        Spawn processes using a Pool with a given pool size.

        Args:
            geometry_path (Path): Path to the folder containing geometry data.
            output_folder (Path): Folder where output files will be written.
            compressed (bool): Flag indicating whether compression is used.
            tolerance (float): Tolerance used in spatial operations.
            min_level (int): Minimum S2 level for processing.
            max_level (int): Maximum S2 level for processing.
            pool_size (int): Number of processes to use in the pool.
        """
        write = partial(
            self.write_all_relations,
            output_folder=output_folder,
            is_compressed=compressed,
            rdf_format=self.rdf_format,
            min_level=min_level,
            max_level=max_level,
            flush_threshold=self.flush_threshold,
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
        flush_threshold: int,
    ) -> None:
        """
        Process geometric features into RDF triples incrementally. When the number of accumulated triples
        reaches flush_threshold, the current graph is written to disk and then reset.

        Args:
            geo_features (GeometricFeatures): The geometric features to process.
            output_folder (str): The folder to write output files.
            is_compressed (bool): Flag indicating if compression is applied.
            rdf_format (str): The RDF serialization format.
            min_level (int): The minimum S2 level to use.
            max_level (int): The maximum S2 level to use.
            flush_threshold (int): The number of triples to accumulate before flushing.
        """
        graph = Graph()
        triple_count = 0
        file_counter = 0

        for geo_feature in geo_features:
            # Log the identifying information for the feature.
            print(f"Processing feature with IRI: {geo_feature.iri}")

            coverer = ConstrainedS2RegionCoverer(min_level, max_level)
            if not is_compressed:
                if min_level:
                    coverer.set_min_level(min_level)
            else:
                coverer.set_min_level(0)

            for s2_triple in geo_feature.yield_s2_relations(coverer):
                graph.add(s2_triple)
                triple_count += 1

                if triple_count >= flush_threshold:
                    filename = f"triples_{file_counter}" + file_extensions[rdf_format]
                    destination = os.path.join(output_folder, filename)
                    print(f"Flushing {triple_count} triples to {destination}")
                    S2Writer.write(graph, Path(destination), rdf_format)
                    # Reset the graph and counters for the next batch.
                    graph = Graph()
                    triple_count = 0
                    file_counter += 1

        # Write any remaining triples that did not reach the threshold.
        if triple_count > 0:
            filename = f"triples_{file_counter}" + file_extensions[rdf_format]
            destination = os.path.join(output_folder, filename)
            print(f"Writing remaining {triple_count} triples to {destination}")
            S2Writer.write(graph, Path(destination), rdf_format)
