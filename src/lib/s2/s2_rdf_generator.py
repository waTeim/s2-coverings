from typing import Generator, List

from rdflib import RDF, RDFS, XSD, Literal, URIRef
from rdflib.namespace._GEO import GEO
from s2geometry import (
    S2Cell,
    S2CellId,
    S2LatLng,
    S2Loop,
    S2Point,
    S2Polygon,
    S2Polyline,
    S2RegionCoverer,
)
from shapely import MultiPolygon
from shapely.geometry import Polygon

from ..rdf.kwg_ont import KWGOnt, generate_cell_iri, get_graph, namespace_prefix


class S2RDFGenerator:
    """
    Abstracts generating a single S2 cell. The class operates from the point of view as
    a single cell. For example, the cell neighbors and parents are relative to the
    cell that the class is instantiated with.
    """

    def __init__(self, cell_id: int, target_parent_level, rdf_format: str):
        self.s2_cell_id = S2CellId(int(cell_id))
        self.s2_cell = S2Cell(self.s2_cell_id)
        self.rdf_format = rdf_format
        self.graph = get_graph()
        self.target_parent_level = target_parent_level
        self.iri = generate_cell_iri(self.s2_cell_id)
        self.create_s2_cell()
        self.add_neighbors()
        self.add_parent_relations()

    def create_s2_cell(self) -> None:
        """
        Creates and adds relations about the cell to the knowledge graph. This includes its
        area, identifier, geometry, etc.
        """
        p = RDF.type
        o = KWGOnt[f"S2Cell_Level{self.s2_cell.level()}"]
        self.graph.add((self.iri, p, o))

        label = (
            f"S2 Cell at level {self.s2_cell.level()} with ID {self.s2_cell_id.id()}"
        )
        p = RDFS.label
        o = Literal(label, datatype=XSD.string)
        self.graph.add((self.iri, p, o))

        p = KWGOnt.cellID
        o = Literal(self.s2_cell_id.id(), datatype=XSD.integer)
        self.graph.add((self.iri, p, o))

        area_on_sphere = self.s2_cell.ApproxArea()
        area_on_earth = area_on_sphere * 6.3781e6 * 6.3781e6

        p = namespace_prefix["geo"]["hasMetricArea"]
        o = Literal(area_on_earth, datatype=XSD.float)
        self.graph.add((self.iri, p, o))

        geometry = self.get_vertex_polygon(cell=self.s2_cell)
        geometry_iri = KWGOnt.KWGR[
            f"geometry.polygon.s2.level{self.s2_cell.level()}.{self.s2_cell_id.id()}"
        ]
        p = GEO.hasGeometry
        self.graph.add((self.iri, p, geometry_iri))

        p = namespace_prefix["geo"]["hasDefaultGeometry"]
        self.graph.add((self.iri, p, geometry_iri))

        p = RDF.type
        o = GEO.Geometry
        self.graph.add((geometry_iri, p, o))

        o = namespace_prefix["sf"]["Polygon"]
        self.graph.add((geometry_iri, p, o))

        label = f"Geometry of the polygon formed from the vertices of the S2 Cell at level {self.s2_cell.level()} with ID {self.s2_cell_id.id()}"
        p = RDFS.label
        o = Literal(label, datatype=XSD.string)
        self.graph.add((geometry_iri, p, o))

        wkt = geometry.wkt
        p = GEO.asWKT
        o = Literal(wkt, datatype=GEO.wktLiteral)
        self.graph.add((geometry_iri, p, o))

    def add_neighbors(self) -> None:
        """
        Computes a cell's neighbors and adds them as graph connections
        """
        neighbors: List[S2CellId] = self.s2_cell_id.GetAllNeighbors(
            self.s2_cell.level()
        )
        for neighbor in neighbors:
            p = KWGOnt.sfTouches
            neighbor_iri = generate_cell_iri(neighbor)

            self.graph.add((self.iri, p, neighbor_iri))
            self.graph.add((neighbor_iri, p, self.iri))

    def add_parent_relations(self):
        """
        Adds relations sfWithin and sfContains to the parent cell
        """
        if 0 < self.s2_cell.level() < 31:
            if self.target_parent_level:
                parent = self.get_parent_at_level(
                    self.s2_cell_id, self.s2_cell.level(), self.target_parent_level
                )
            else:
                parent = self.s2_cell_id.parent()
            parent_iri = generate_cell_iri(parent)
            p = KWGOnt.sfWithin
            self.graph.add((self.iri, p, parent_iri))

            p = KWGOnt.sfContains
            self.graph.add((parent_iri, p, self.iri))

    def get_parent_at_level(self, cell, current_cell_level: int, target_level: int):
        """
        Gets a parent S2 cell at some level ABOVE the current one. By above it
        is meant that it contains the s2 level. For example,
        current_cell_level = 4
        target_level=2
        You will get the S2 cell in level 2
        """
        while target_level < cell.level():
            current_cell_level = current_cell_level - 1
            cell = self.get_parent_at_level(
                cell.parent(), current_cell_level, target_level
            )
        return cell

    @staticmethod
    def get_vertex_polygon(cell: S2Cell) -> Polygon:
        """
        Unknown
        """
        vertices = map(cell.GetVertex, range(4))
        lat_lngs = [S2LatLng(vertex) for vertex in vertices]
        coords = [
            [lat_lng.lng().degrees(), lat_lng.lat().degrees()] for lat_lng in lat_lngs
        ]
        vertex_polygon = Polygon(coords)
        return vertex_polygon
