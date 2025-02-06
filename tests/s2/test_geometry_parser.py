from pathlib import Path

from src.lib.geometry_parser import GeometryParser


def test_init():
    """
    Test that the path to the geofile is being persisted
    """
    geo_path = Path("./data/test_geo.ttl")
    geo_parser = GeometryParser(geo_path)
    assert geo_parser.path == geo_path


def test_results():
    """
    Test that the correct
    """
    geo_path = Path("./data/test_geo.ttl")
    geo_parser = GeometryParser(geo_path)
    # mock os.open
