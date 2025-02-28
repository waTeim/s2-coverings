from pathlib import Path
from unittest.mock import patch

import rdflib

from src.lib.geo.geometric_features import GeometricFeatures


@patch("src.lib.geo.geometry_parser.GeometryParser.parse")
def test_iter(parser_mock):
    """
    Test that the inner GeometricFeature instances can be
    iterated over (as an iterator).
    """
    parser_mock.return_value = [
        {
            "feature_iri": rdflib.term.URIRef(
                "http://stko-kwg.geog.ucsb.edu/lod/resource/geometry.polygon.s2.level1.10088063165309911040"
            ),
            "wkt": rdflib.term.Literal(
                "POLYGON ((-90 45, -90 0, -45 0, -45 35.264389682754654, -90 45))",
            ),
        },
        {
            "feature_iri": rdflib.term.URIRef(
                "http://stko-kwg.geog.ucsb.edu/lod/resource/geometry.polygon.s2.level1.10664523917613334528"
            ),
            "wkt": rdflib.term.Literal(
                "POLYGON ((-90 0, -90 -45, -45 -35.264389682754654, -45 0, -90 0))",
            ),
        },
    ]
    geo_feautres = GeometricFeatures(Path('not_real_path'), 1,1 , 1)
    features = list(geo_feautres)
    assert len(features) == 2
