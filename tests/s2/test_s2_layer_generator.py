from unittest.mock import patch

from s2geometry import S2CellId

from src.lib.s2.s2_layer_generator import S2LevelGenerator


@patch("src.lib.s2.s2_layer_generator.S2LevelGenerator.spawn_processes")
@patch("src.lib.rdf.s2_writer.S2Writer.create_output_path")
def test_init(output_mock, spawn_mock):
    """
    Tests that the ctor creates the output folder
    and spawns the processes
    """
    S2LevelGenerator(1, "ttl", 10, 1, "output")
    output_mock.assert_called_once()
    spawn_mock.assert_called_once()


@patch("src.lib.rdf.s2_writer.S2Writer.create_output_path")
@patch("src.lib.rdf.s2_writer.S2Writer.write")
def test_generate_and_write(write_mock, create_output_mock):
    """
    Tests that the rdf generator is able to generate
    rdf, given s2 cell ids and write them
    """
    # Generate 2 S2 cell ids
    ids = []
    cell_itr = S2CellId.Begin(level=2)
    ids.append(cell_itr.next().id())
    ids.append(cell_itr.next().id())
    level_generator = S2LevelGenerator(2, "ttl", 10, 1, "output")
    level_generator.generate_and_write(ids)
    write_mock.assert_called_once()
    create_output_mock.assert_called_once()


@patch("src.lib.rdf.s2_writer.S2Writer.create_output_path")
@patch("multiprocessing.pool.Pool.imap_unordered")
def test_spawn_processes(pool_mock, create_output_mock):
    """
    Tests that the spawn processes calls multiprocessing
    """
    pool_mock.return_value = []
    level_generator = S2LevelGenerator(2, "ttl", 10, 1, "output")
    level_generator.spawn_processes()
    create_output_mock.assert_called_once()


@patch("src.lib.s2.s2_layer_generator.S2LevelGenerator.spawn_processes")
@patch("src.lib.rdf.s2_writer.S2Writer.create_output_path")
def test_generate_cells_at_level_no_chunk(output_mock, spawn_mock):
    """
    Tests that cells are being generated at a level
    """
    level_generator = S2LevelGenerator(0, "ttl", 10, 1, "output")
    res = level_generator.generate_cells_at_level()
    res = list(res)
    # Check that there's one chunk
    assert len(res) == 1
    # level 0 has six cells
    assert len(res[0]) == 6


@patch("src.lib.s2.s2_layer_generator.S2LevelGenerator.spawn_processes")
@patch("src.lib.rdf.s2_writer.S2Writer.create_output_path")
def test_generate_cells_at_level(output_mock, spawn_mock):
    """
    Tests that cells are being generated at a
    level and are being chunked
    """
    level_generator = S2LevelGenerator(0, "ttl", 1, 1, "output")
    res = level_generator.generate_cells_at_level()
    res = list(res)
    for a in res:
        print(a)
    # Check that there's six chunks
    assert len(res) == 6
