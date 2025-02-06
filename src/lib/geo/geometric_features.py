from pathlib import Path

from .geometric_feature import GeometricFeature
from .geometry_parser import GeometryParser


class GeometricFeatures:
    def __init__(self, path: Path, tolerance, min_level, max_level) -> None:
        """
        Create a new GeometricFeatures
        """
        self.path = path
        self.tolerance = tolerance
        self.min_level = min_level
        self.max_level = max_level

    def __iter__(self):
        """ """
        for solution in GeometryParser.parse(self.path):
            iri = solution["feature_iri"]
            geometry = loads(solution["wkt"])
            yield GeometricFeature(
                geometry, iri, self.tolerance, self.min_level, self.max_level
            )

    def __next__(self):
        """
        Iterates to the next geometric feature
        """
        solution = GeometryParser.parse(self.path)
        iri = solution["feature_iri"]
        geometry = loads(solution["wkt"])
        yield GeometricFeature(
            geometry, iri, self.tolerance, self.min_level, self.max_level
        )
