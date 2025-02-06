from __future__ import annotations

import logging
import os
import time
from multiprocessing import current_process
from pathlib import Path

from rdflib import Graph


class S2Writer:
    """
    Responsible for managing the process of writing graphs to disk.
    This includes creating the directories and writing the graph objects
    """

    def __init__(self):
        """
        Create a new S2Writer
        """

    @staticmethod
    def create_output_path(level: Path | None, output_path: Path):
        """
        Creates the directory path to where the rdf files will be written to.

        :param level: The s2 level that's being written
        :param output_path: The top level output folder
        """
        if level is not None:
            output_path_level = Path(f"level_{level}")
            output_path = os.path.join(output_path, output_path_level)
        os.makedirs(output_path, exist_ok=True)

    @staticmethod
    def write(graph: Graph, output_path: Path, rdf_format: str):
        """
        Writes a knowledge graph to disk

        :param graph: The graph being written
        :param filepath: Path where the file will be written to
        :param rdf_format: The rdf format of the file
        """
        start_time = time.time()
        logging.debug(f"{current_process()}: Starting write")
        graph.serialize(output_path, format=rdf_format)
        logging.debug(
            f"{current_process()}: Ended write. Duration: {time.time() - start_time}"
        )
