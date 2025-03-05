# s2-coverings
Tool for creating index-free s2 coverings, at any level

## Background

[S2](http://s2geometry.io/) is a spatial grid system with hierarchy, designed to be easily indexed and queried. Knowledge graphs commonly make use of geospatial indices as ways to connect geospatial data.


Rather than relying on geosparql functions (which in turn rely on geosparql support), you can instead 
1. Generate the global spatial index (create s2 cells, as rdf statements)
2. Pre-materialize the relations between cells (connect s2 cells with RCC8 relations)
3. Integrate your own geometries with the S2 cells (connect the geometry to s2  cells with RCC*)

This breaks the reliance on the need for the graph database to support s2 indexing and instead make use of the predicate index from the pre-materialized spatial relations.

## Cell Generation and Integration

There are two tools:

1. s2.py: This generates the S2 cell structure at a desired layer, or for an existing set of geometries 
2. integrate.py: This performs s2 integrations against existing geometries. These may be your own geometries, they may be the output of the s2 tool. 


## Running
The project dependencies can be difficult to install; docker images are provided so that the code can be run in different environments without needing to install dependencies. Rather than offering a docker image for each cript, both scripts are included in the image and they can be called externally

### Generating S2 Cells for a Level

Given a target S2 level, the s2 generation script will generate s2 cells at the target level. 

**Current Production image**
```bash
docker run -v ./:/s2 ghcr.io/knowwheregraph/s2-coverings:main python3 src/s2.py --level <level>
```

**Running locally**
```commandline
git clone
cd s2-coverings
docker build -t s2-coverings .
docker run -v ./:/s2 s2-coverings python3 src/s2.py --level 2
```

### Generating S2 Cells Over a Geometry

Given a folder of RDF that describes s2 cells under the geosparql ontology, it's possible to generate new RDF of all the
S2 cells that overlap the geometry at a certain level.

The level is dictated by the min_level and max_level cli arguments. _These should be the same value_.

**Current Production image**
```bash
docker run -v ./:/s2 ghcr.io/knowwheregraph/s2-coverings:main python3 src/s2.py --path <path_to_geometries> --output_path=output/ --min_level=5 --max_level=5
```

**Running locally**
```commandline
git clone
cd s2-coverings
docker build -t s2-coverings .
docker run -v ./:/s2 s2-coverings python3 src/s2.py --geometry_path <path_to_geometries> --output_path=output/ --min_level=5 --max_level=5
```

### Integrating S2 Cells With Another Layer 

Given a folder of S2 cells, described with the geosparql ontology, it's possible to create the following spatial relations between the s2 cells
on disk and the layer of your choice.
The primary relation materialized through this process is `kwg-ont:sfWithin`. This effectively "connects" the S2 cells with the target layer.

**Current Production image**
```bash
docker run -v ./:/s2 ghcr.io/knowwheregraph/s2-coverings:main python3 src/integrate.py --path <path to geometries>
```

**Using locally**
```commandline
git clone
cd s2-coverings
docker build -t s2-coverings .
docker run -v ./:/s2 s2-coverings python3 src/integrate.py --path some_path_to_data

```

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