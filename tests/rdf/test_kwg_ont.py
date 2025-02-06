from rdflib import URIRef
from s2geometry import S2CellId

from src.lib.rdf.kwg_ont import generate_cell_iri, get_graph


def test_generate_cell_iri():
    """
    Tests to ensure the S2 cell IRI is the expected form

    :return: None
    """
    cell_id_int = 288230376151711744
    cell_id = S2CellId(cell_id_int)
    assert generate_cell_iri(cell_id) == URIRef(
        "http://stko-kwg.geog.ucsb.edu/lod/resource/s2.level1" ".288230376151711744"
    )


def test_get_graph():
    """
    Tests that a new graph with prefixes is returned. Test this
    by looking for the geosparql namespace, which isn't in defualt
    rdflib graphs.
    """
    g = get_graph()
    found_geosparql = False
    for ns_prefix, namespace in g.namespaces():
        print(ns_prefix)
        if "geo" == ns_prefix:
            found_geosparql = True
    if not found_geosparql:
        raise AssertionError("Failed to find the geosparql namesapce in the default graph")
