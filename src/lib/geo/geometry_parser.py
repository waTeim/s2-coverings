import os
from pathlib import Path
from typing import Any, Generator

from rdflib import Graph
from rdflib.query import ResultRow


class GeometryParser:
    """
    Parses files that represent geometries and returns the features from it. The
    class is stateless.
    """

    def __init__(self):
        """
        Empty ctor for the stateless class
        """

    @staticmethod
    def get_files(directory):
        for path, _, files in os.walk(directory):
            print(files)
            for file in files:
                if not file == ".DS_Store":
                    file_path = os.path.join(path, file)
                    yield file_path

    @staticmethod
    def parse(path: Path) -> Generator[ResultRow, Any, None]:
        """
        Parses an RDF file for geometries, specified under the geosparql ontology

        :param path: Path to the file, which should contain a geometry
        :return: A row of results from the query
        """
        graph = Graph()
        for file in GeometryParser.get_files(path):
            print("Parsing file {}".format(file))
            with open(file, "r") as read_stream:
                graph.parse(read_stream)
            result = graph.query(
                """
                PREFIX geo: <http://www.opengis.net/ont/geosparql#>
                SELECT ?feature_iri ?wkt 
                WHERE {
                    ?feature_iri geo:hasGeometry ?geometry .
                    ?geometry geo:asWKT ?wkt .
                }
                """
            )
            for query_solution in result:
                yield query_solution
