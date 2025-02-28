import argparse
import logging
import time

from lib.s2.s2_layer_generator import S2LevelGenerator
from lib.s2.s2_overlap_generator import S2OverlapGenerator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--level", type=int, help="Level at which the s2 cells are generated for"
    )
    parser.add_argument(
        "--format",
        help="The format to write the RDF in. Options are xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, "
        "json-ld, hext",
        type=str,
        nargs="?",
        default="ttl",
    )
    parser.add_argument(
        "--target_parent_level",
        help="The highest s2 level to integrate with.",
        type=int,
        nargs="?",
        default="-1",
    )
    parser.add_argument(
        "--batch_size",
        help="The number of s2 cells to include in a single output file. Larger"
        "numbers (100000+) are recommended for levels 10 and higher to reduce the number"
        "of files written. The increase in count comes with an increased memory footprint.",
        type=int,
        nargs="?",
        default="100000",
    )
    parser.add_argument(
        "--output_path",
        help="The path to where the files will be written to. Default is ./output",
        type=str,
        nargs="?",
        default="./output/",
    )
    parser.add_argument(
        "--geometry_path",
        help="The path to geometry files, which will be used to generate s2 cells",
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "--min_level",
        help="The level where generation starts.",
        type=int,
        nargs="?",
        default=5,
    )
    parser.add_argument(
        "--max_level",
        help="The s2 level where generation ends.",
        type=int,
        nargs="?",
        default=5,
    )
    parser.add_argument(
        "--tolerance",
        help="Tolerance used during spatial operations. Defaults to 1e-2",
        type=float,
        nargs="?",
        default=1e-2,
    )

    args = parser.parse_args()

    if args.geometry_path:
        S2OverlapGenerator(
            args.geometry_path,
            args.format,
            args.tolerance,
            args.min_level,
            args.max_level,
            args.output_path,
            args.batch_size,
        )
        exit()
    parent_level = args.target_parent_level
    if parent_level < 0:
        parent_level = None

    start_time = time.time()
    logging.debug("Starting S2 Cell generation")
    S2LevelGenerator(
        args.level, args.format, args.batch_size, parent_level, args.output_path
    )
    logging.debug(f"Ended S2 Cell generation: Duration {time.time() - start_time}")
