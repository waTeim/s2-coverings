from __future__ import annotations

from functools import partial
from typing import Generator, Optional

from rdflib import URIRef
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
from shapely import (
    LinearRing,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
    buffer,
)
from shapely.geometry.polygon import signed_area

from ..rdf.kwg_ont import KWGOnt, generate_cell_iri
from .constrained_s2_region_converer import ConstrainedS2RegionCoverer


class GeometricFeature:
    """
    Represents a geometric feature, which has a wkt geometry and IRI. Has several methods related
    to geometry calculations that don't fit in elsewhere.
    """

    def __init__(self, geometry, IRI, tolerance: float, min: int, max: int) -> None:
        """
        Create a new GeometricFeature
        """

        self.tolerance = tolerance
        self.min = min
        self.max = max
        self.geometry = geometry
        self.iri = IRI

    @staticmethod
    def orient(
        geometry: LinearRing | Polygon | MultiPolygon, sign: Optional[float] = 1.0
    ) -> LinearRing | Polygon | MultiPolygon:
        """
        Returns a copy of the geometry with the specified orientation

        :param geometry: The geometyry being oriented
        :param sign: (float, optional): an orientation. Defaults to 1.0.
        Returns:
            LinearRing | Polygon | MultiPolygon: a copy of the geometry with specified orientation
        """
        sign = float(sign)
        if isinstance(geometry, LinearRing):
            return geometry if signed_area(geometry) / sign >= 0 else geometry.reverse()
        elif isinstance(geometry, Polygon):
            exterior = GeometricFeature.orient(geometry.exterior, sign)
            oppositely_orient = partial(GeometricFeature.orient, sign=-sign)
            interiors = list(map(oppositely_orient, geometry.interiors))
            return Polygon(exterior, interiors)
        elif isinstance(geometry, MultiPolygon):
            orient_with_sign = partial(GeometricFeature.orient, sign=sign)
            return MultiPolygon(list(map(orient_with_sign, geometry.geoms)))

    @staticmethod
    def boundaries(
        geometry: Polygon | MultiPolygon,
    ) -> Generator[LinearRing, None, None]:
        """
        Yields the boundary rings of a geometry with boundaries

        :param geometry: A shapely geometry with boundaries
        :return: A generator through the boundary rings
        """
        polygons = []
        if isinstance(geometry, Polygon):
            polygons = [geometry]
        elif isinstance(geometry, MultiPolygon):
            polygons = geometry.geoms
        for polygon in polygons:
            yield polygon.exterior
            for interior in polygon.interiors:
                yield interior

    def yield_overlapping_ids(self) -> Generator[S2CellId, None, None]:
        """yields the cell IDs of those that overlap
        the given 2D geometry to a certain value of tolerance, at a certain level

        Args:
            geometry (Polygon | MultiPolygon): a 2-dimensional geometry
        Yields:
            Generator[S2CellId, None, None]: a generator through the overlapping IDs
        """

        for boundary in GeometricFeature.boundaries(self.geometry):
            segmented_boundary = boundary.segmentize(self.tolerance)
            buff = buffer(segmented_boundary, self.tolerance / 100, 2)
            for cell_id in self.covering_with_geo(
                buff,
                coverer=ConstrainedS2RegionCoverer(self.min, self.max),
            ):
                yield cell_id

    def yield_crossing_ids(
        self,
        line_obj: LineString | MultiLineString,
    ) -> Generator[S2CellId, None, None]:
        """Yields those Cell IDs  covering a small (multi)polygon buffer around the given (multi)line string
        to a certain degree of tolerance. The buffer is constructed
        so that its border is at a distance of tolerance/100 from the
        (multi)line string.

        Args:
            line_obj (LineString | MultiLineString): a 1D geometry
        Yields:
            Generator[S2CellId, None, None]: a generator of crossing cell IDs
        """

        buff = buffer(line_obj, self.tolerance / 100, 2)
        for cell_id in self.covering_with_geo(
            buff, ConstrainedS2RegionCoverer(self.min, self.max)
        ):
            yield cell_id

    def s2_approximation(
        self,
        geometry: S2Point | LinearRing | LineString | Polygon | MultiPolygon,
    ) -> S2Point | S2Loop | S2Polyline | S2Polygon:
        """
        Returns a corresponding S2 object that approximates the given
        Shapely object to a certain value of tolerance. Precisely, a given
        Shapely geometry is first segmentized, meaning extra vertices are added
        so that the width between any two adjacent vertices never exceeds the
        tolerance, and then these new coordinates are used as the vertices
        of an S2 object (see s2_from_coords).
        Args:
            geometry (LinearRing | LineString | Polygon | MultiPolygon): a Shapely geometry
        Returns:
            S2Point | S2Loop | S2Polyline | S2Polygon: an S2 geometry object
        """
        return self.s2_from_coords(geometry)

    def s2_from_coords(
        self,
        geometry: Point | LinearRing | LineString | Polygon | MultiPolygon,
    ) -> S2Point | S2Loop | S2Polyline | S2Polygon:
        """
        Returns a corresponding S2 object whose vertices
        are obtained from the coordinates of the given geometry.
        Note that the returned object lives on the sphere and any
        linear edges are replaced by geodesic curves. As such, the resulting
        S2 object is an APPROXIMATION of the given geometry living on
        the sphere, and the approximation is worse when vertices are farther apart
        (because geodesics will curve more in that case).
        Args:
            geometry (tuple | Point | LinearRing | LineString | Polygon | MultiPolygon): a geometry
        Returns:
            S2Point | S2Loop | S2Polyline | S2Polygon: an S2 geometric object
        """
        if isinstance(geometry, tuple):
            return S2LatLng.FromDegrees(*geometry[::-1]).ToPoint()
        elif isinstance(geometry, Point):
            return S2LatLng.FromDegrees(*geometry.coords[0][::-1]).ToPoint()
        elif isinstance(geometry, LinearRing):
            s2_loop = S2Loop()
            s2_loop.Init(list(map(self.s2_from_coords, list(geometry.coords)[:-1])))
            return s2_loop
        elif isinstance(geometry, LineString):
            polyline = S2Polyline()
            polyline.InitFromS2Points(list(map(self.s2_from_coords, geometry.coords)))
            return polyline
        elif isinstance(geometry, (Polygon, MultiPolygon)):
            loops = map(
                self.s2_from_coords,
                map(self.orient, GeometricFeature.boundaries(geometry)),
            )
            s2_polygon = S2Polygon()
            s2_polygon.InitNested(list(loops))
            return s2_polygon

    def filling(
        self,
        polygon: Polygon | MultiPolygon,
        coverer: S2RegionCoverer,
    ) -> list[S2CellId]:
        """
        Returns a list of cell IDs that constitute a filling
        of a 2-dimensional geometry that is saturated to the 13th level
        within a certain value of tolerance

        Args:
            polygon (Polygon | MultiPolygon): a 2-dimensional geometry
            coverer (S2RegionCoverer):
        Returns:
            list[S2CellId]: a list of s2 cell IDs in a saturated fill
        """
        filling = []
        s2_obj = self.s2_approximation(polygon)
        for exponent in range(4, 9):
            max_cells = 10**exponent
            coverer.set_max_cells(max_cells)
            filling = coverer.GetInteriorCovering(s2_obj)
            num_cells = len(filling)
            if num_cells < 10 ** (exponent - 1):
                break  # iterate until the filling is saturated
        return filling

    def covering(
        self,
        coverer: S2RegionCoverer,
    ) -> list[S2CellId]:
        """Returns a covering of a batch of s2 cell IDs appearing in a homogeneous
        covering of a 2-dimensional geometry to a certain value of tolerance
        Args:
            coverer:
        Returns:
            list[S2CellId]: A list of s2 cell IDs that cover the geometry
        """
        s2_obj = self.s2_approximation(self.geometry)
        covering = coverer.GetCovering(s2_obj)
        return covering

    def covering_with_geo(
        self,
            geometry: Point | LinearRing | LineString | Polygon | MultiPolygon,
        coverer: S2RegionCoverer,
    ) -> list[S2CellId]:
        """Returns a covering of a batch of s2 cell IDs appearing in a homogeneous
        covering of a 2-dimensional geometry to a certain value of tolerance
        Args:
            coverer:
        Returns:
            list[S2CellId]: A list of s2 cell IDs that cover the geometry
        """
        s2_obj = self.s2_approximation(geometry)
        covering = coverer.GetCovering(s2_obj)
        return covering

    def yield_s2_relations(
        self, coverer: S2RegionCoverer
    ) -> Generator[tuple[URIRef, URIRef, URIRef], None, None]:
        """
        Given an s2 coverer, generate rdf s2 cells and several relations
        connecting them to other cells

        :param coverer: A covering
        :return: A generator of tuples, representing a semantic triple
        """
        if isinstance(self.geometry, (Polygon, MultiPolygon)):
            predicate = KWGOnt.sfContains
            inverse = KWGOnt.sfWithin
            for cell_id in self.filling(self.geometry, coverer):
                yield self.iri, predicate, generate_cell_iri(cell_id)
                yield generate_cell_iri(cell_id), inverse, self.iri

            predicate = KWGOnt.sfOverlaps
            for cell_id in self.yield_overlapping_ids():
                yield self.iri, predicate, generate_cell_iri(cell_id)
                yield generate_cell_iri(cell_id), predicate, self.iri

        elif isinstance(self.geometry, (LineString, MultiLineString)):
            predicate = KWGOnt.sfCrosses
            for cell_id in self.yield_crossing_ids(self.geometry):
                yield self.iri, predicate, generate_cell_iri(cell_id)
                yield generate_cell_iri(cell_id), predicate, self.iri

        elif isinstance(self.geometry, Point):
            s2_point = self.s2_from_coords(self.geometry)
            cell_id = S2CellId(s2_point).parent()
            yield self.iri, KWGOnt.sfWithin, generate_cell_iri(cell_id)
            yield generate_cell_iri(cell_id), KWGOnt.sfContains, self.iri
        else:
            geom_type = self.geometry.geom_type
            msg = f"Geometry of type {geom_type} not supported for s2 relations"
            raise ValueError(msg)
