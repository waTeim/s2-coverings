from rdflib import RDF, RDFS, XSD, Graph, URIRef
from rdflib.namespace import DefinedNamespace, Namespace
from s2geometry import S2Cell, S2CellId


class KWGOnt(DefinedNamespace):
    kwg_endpoint = "http://stko-kwg.geog.ucsb.edu/"

    KWGR = Namespace(f"{kwg_endpoint}lod/resource/")

    S2Cell_Level0: URIRef
    S2Cell_Level1: URIRef
    S2Cell_Level2: URIRef
    S2Cell_Level3: URIRef
    S2Cell_Level4: URIRef
    S2Cell_Level5: URIRef
    S2Cell_Level6: URIRef
    S2Cell_Level7: URIRef
    S2Cell_Level8: URIRef
    S2Cell_Level9: URIRef
    S2Cell_Level10: URIRef
    S2Cell_Level11: URIRef
    S2Cell_Level12: URIRef
    S2Cell_Level13: URIRef

    cellID: URIRef

    sfEquals: URIRef
    sfContains: URIRef
    sfWithin: URIRef
    sfTouches: URIRef
    sfOverlaps: URIRef
    sfCrosses: URIRef
    vertexPolygon: URIRef

    _NS = Namespace(f"{kwg_endpoint}lod/ontology/")


def generate_cell_iri(cell_id: S2CellId) -> URIRef:
    """
    Creates an IRI for an individual cell, with a KnowWhereGraph domain

    :param cell_id: The ID of the s2 cell
    :return: A URI representing the s2 cell
    """
    level = cell_id.level()
    id_str = str(cell_id.id())
    return KWGOnt.KWGR[f"{'s2.level'}{level}.{id_str}"]


namespace_prefix = {
    "kwgr": KWGOnt.KWGR,
    "kwg-ont": KWGOnt._NS,
    "geo": Namespace("http://www.opengis.net/ont/geosparql#"),
    "sf": Namespace("http://www.opengis.net/ont/sf#"),
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD,
}

file_extensions = {
    "ttl": ".ttl",
    "turtle": ".ttl",
    "xml": ".xml",
    "nq": ".nq",
    "n3": "n3",
    "nt": ".nt",
    "trix": ".trix",
    "trig": ".trig",
    "nquads": ".nq",
    "json-ld": ".jsonld",
}


def get_graph() -> Graph:
    """
    Gets an rdflib graph with the prefixes used by the project

    :return: A standard graph object
    """
    graph = Graph()
    for pfx in namespace_prefix:
        graph.bind(pfx, namespace_prefix[pfx])
    return graph
