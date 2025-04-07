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
        flush_threshold: int = 50000,  # Number of triples to accumulate before flushing
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
       # Ensure geo_features is a list for slicing.
        geo_features = list(GeometricFeatures(geometry_path, tolerance, min_level, max_level))
        # Partition the geo_features into exactly pool_size sublists.
        partitions = [geo_features[i::pool_size] for i in range(pool_size)]
        # Pair each partition with a process ID.
        partitioned_data = list(enumerate(partitions))  # Each element is a tuple: (process_id, features_subset)
        write = partial(
            self.write_all_relations_batch,
            output_folder=output_folder,
            is_compressed=compressed,
            rdf_format=self.rdf_format,
            min_level=min_level,
            max_level=max_level,
            flush_threshold=self.flush_threshold,
        )
        with Pool(processes=pool_size) as pool:
            pool.map(write, partitioned_data)

    def write_all_relations_batch(
        self,
        data: tuple,
        output_folder: str,
        is_compressed: bool,
        rdf_format: str,
        min_level: int,
        max_level: int,
        flush_threshold: int,
    ) -> None:
        # Unpack the tuple: process_id and its assigned features.
        process_id, features_subset = data
        graph = Graph()
        triple_count = 0
        file_counter = 0
        feature_count = 0

        print(f"[Process {process_id}] Starting processing of {len(features_subset)} features.")

        for feature in features_subset:
            feature_count += 1
            #print(f"[Process {process_id}] Processing feature with IRI: {feature.iri}")
            coverer = ConstrainedS2RegionCoverer(min_level, max_level)
            if not is_compressed:
                if min_level:
                    coverer.set_min_level(min_level)
            else:
                coverer.set_min_level(0)

            for s2_triple in feature.yield_s2_relations(coverer):
                graph.add(s2_triple)
                triple_count += 1

                if triple_count >= flush_threshold:
                    filename = f"proc_{process_id}_batch_{file_counter}" + file_extensions[rdf_format]
                    destination = os.path.join(output_folder, filename)
                    print(f"[Process {process_id}] Flushing {triple_count} triples to {destination}")
                    S2Writer.write(graph, Path(destination), rdf_format)
                    graph = Graph()  # Reset the graph.
                    triple_count = 0
                    file_counter += 1

        if triple_count > 0:
            filename = f"proc_{process_id}_batch_{file_counter}" + file_extensions[rdf_format]
            destination = os.path.join(output_folder, filename)
            print(f"[Process {process_id}] Writing remaining {triple_count} triples to {destination}")
            S2Writer.write(graph, Path(destination), rdf_format)

        print(f"[Process {process_id}] Finished processing features count={feature_count}")