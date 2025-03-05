from pathlib import Path
from unittest.mock import patch

import pytest
from rdflib import Graph

from src.lib.rdf.s2_writer import S2Writer


def test_init():
    """
    Tests that it's not possible to instantiate an RDF Writer.
    If NotImplementedError isn't
    """
    with pytest.raises(NotImplementedError):
        S2Writer()


@patch("os.makedirs")
def test_create_output_path_none(dir_patch):
    """
    Tests that the output folder is correctly
    created for writes that don't include levels
    """
    path = Path("fake_output_path")
    S2Writer.create_output_path(None, path)
    dir_patch.assert_called_once()


@patch("os.makedirs")
def test_create_output_path(dir_patch):
    """
    Tests that the output folder is correctly
    created for writes tha include levels
    """
    path = Path("fake_output_path")
    level = 1
    S2Writer.create_output_path(level, path)
    dir_patch.assert_called_once()


@patch("rdflib.Graph.serialize")
def test_write(graph_patch):
    """
    Tests that the RDF writer correctly
    writes rdf to disk
    """
    path = Path("fake_output_path")
    S2Writer.write(Graph(), path, "ttl")
    graph_patch.assert_called_once()
