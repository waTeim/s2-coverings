import os
from multiprocessing import Pool
from pathlib import Path
from typing import List

from rdflib import Graph
from s2geometry import S2Cell, S2CellId

from ..rdf.s2_writer import S2Writer
from .s2_rdf_generator import S2RDFGenerator
from ..rdf.kwg_ont import file_extensions


class S2LevelGenerator:
    """
    Abstracts generating a level of S2 Cells
    """

    def __init__(
        self, level, rdf_format, batch_size, target_parent_level, output_path: Path
    ):
        """
        :param level: The S2 level the instance represents
        :param rdf_format: The desired format the child cells to be in
        :param chunk_size: The number of cells to include in a single file
        :param target_parent_level: The parent level to integrate with
        :param output_path:

        Create a new level generator
        """
        self.level = level
        self.rdf_format = rdf_format
        self.target_parent_level = target_parent_level
        self.batch_size = batch_size
        self.output_path = output_path
        S2Writer.create_output_path(level, output_path)
        # Create the new processes, which will generate the cells
        self.spawn_processes()

    def generate_and_write(self, cell_ids: [int]) -> None:
        """
        The entry point for each new process. This method first generates the rdf representation
        of each s2 cell. Then, they're written to disk together in a single file.

        :param cell_ids: A list of S2 cells; an rdf serialization will be generated for each
        """
        graph = Graph()
        for cell_id in cell_ids:
            rdf_cell = S2RDFGenerator(
                cell_id, self.target_parent_level, self.rdf_format
            )
            graph += rdf_cell.graph

        # Once the batch is processed, write the file
        filepath = os.path.join(

            self.output_path, f"level_{self.level}", f"{str(cell_ids[0])}{file_extensions[self.rdf_format]}"
        )

        S2Writer.write(graph, Path(filepath), self.rdf_format)

    def spawn_processes(self) -> None:
        """
        Creates new processes, each processing a batch of S2 cell identifiers
        """
        with Pool() as pool:
            # Use a for loop to block async behavior
            for res in pool.imap_unordered(
                self.generate_and_write, self.generate_cells_at_level()
            ):
                pass

    def generate_cells_at_level(self) -> List[str]:
        """
        Generates a chunked list of all the s2 cells in the current level.
        The list is chunked into groups of s2 cells. Each group will be processed separately
        The Multiprocessing modules pickles any data sent to the new process, and one of the
        s2 objects can't be picked. So rather than passing the argument, its numeric id is
        provided instead.

        :return
        """
        # Get the current and end ID to eventually iterate between
        current_id = S2CellId.Begin(level=self.level)
        ending_id = S2CellId.End(level=self.level)
        id_batch = []
        # The maximum number of cells to put in a minibatch
        # Ending id is not a valid s2 id
        while current_id != ending_id:
            id_batch.append(str(current_id.id()))
            # If the threshold is met, add the mini batch to the full
            # batch and clear the mini batch for the next iteration
            if len(id_batch) == self.batch_size:
                current_id = current_id.next()
                yield id_batch
                id_batch = []
            current_id = current_id.next()
        yield id_batch
