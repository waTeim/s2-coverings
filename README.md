# s2-coverings
Tool for creating index-free s2 coverings, at any level

## Background

[S2](http://s2geometry.io/) is a spatial grid system with hierarchy, designed to be easily indexed and queried. Knowledge graphs commonly make use of different geospatial indices for linking spatial data to areas.

At the moment, many graph databases don't have native support for making use of the s2 index system. That's where this tool comes into play.

Rather than relying on geosparql functions (which in turn rely on geosparql support and indices), you can instead pre-materialize the relations between cells and query them though the KnowWhereGraph ontology.

This breaks the reliance on the need for the graph database to support s2 indexing and instead make use of the predicate index from the pre-materialized spatial relations.

## Cell Generation and Integration

There are two tools:

1. s2.py: This generates the S2 cell structure at a desired layer. For example, generating cells at level 3 and 4.
2. integrate.py: This performs s2 integrations against existing geometries. These may be your own geometries, they may be the output of the s2 tool. 

## Running

### Docker

The project dependencies can be difficult to install; docker images are provided so that the code can be run in different environments without needing to install dependencies. Rather than offering a docker image for each cript, both scripts are included in the image and they can be called externally

#### Generating S2 Cells

```bash
git clone https://github.com/KnowWhereGraph/s2-coverings.git
cd s2-coverings
docker run -v ./:/s2 ghcr.io/knowwheregraph/s2-coverings:main python3 src/s2.py --level <level>
```

#### S2 Integration


```bash
docker run -v ./:/s2 ghcr.io/knowwheregraph/s2-coverings:main python3 src/integrate.py --path <path to geometries>
```

A complete list of options can be found by running the help command on each tool. For example,
```bash
python3 src/s2.py --help
options:
  -h, --help            show this help message and exit
  --level LEVEL         Level at which the s2 cells are generated for
  --format [FORMAT]     The format to write the RDF in. Options are xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, json-ld, hext
  --compressed [COMPRESSED]
                        use the S2 hierarchy to write a compressed collection of relations at various levels
```
Results will be written to the `output/` folder. The results can then be loaded into your graph database and queried. For more information on querying with the KnowWhereGraph ontology, visit the [docs site](https://knowwheregraph.github.io/#/).

### Locally

Due to the steps involved with installing the s2 libray bindings and different approaches needed for each architecture - running outside of Docker isn't supported. If you're inspired, the Dockerfile has all necessary steps to install the requirements to run the tool.

## Development

### Running Locally With Docker

During development, you'll need a way to run the local codebase with your changes. To do this run the following, 

```bash
docker compose up -d
docker exec -it s2 bash
python3 src/s2.py --level <s2_level>
```

The source code in the container will stay up to date with the local filesystem, so there's no need to rebuild the image after each code change.

### Linting

This repository adheres to the Black tool's default settings. It also makes use of isort for import sorting.  Run these before each pull request. 

**Black and isort are competing for formatting the imports differently**. Run isort _after_ running black.

```commandline
black .
isort .
```

### Tests

Unit tests should be run before each pull request. To run them,

`pytest`

### Contributing

Contributions are welcome! Before working on any new features, please file an issue to make sure the work is in scope with this project. New code should be submitted as a pull request to the `develop` branch.