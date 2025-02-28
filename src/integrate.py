from __future__ import annotations

import argparse
from pathlib import Path

from lib.integration.integrator import Integrator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        help="Path to the folder with triples being integrated",
        type=str,
        nargs="?",
        default="./output",
    )
    parser.add_argument(
        "--output_path",
        help="The path to where the files will be written to. Default is ./output",
        type=Path,
        nargs="?",
        default="/output/",
    )
    parser.add_argument(
        "--compressed",
        help="use the S2 hierarchy to write a compressed collection of relations at various levels",
        type=bool,
        nargs="?",
        default=False,
    )
    parser.add_argument(
        "--tolerance",
        help="Tolerance used during spatial operations. Defaults to 1e-2",
        type=float,
        nargs="?",
        default=1e-2,
    )
    parser.add_argument(
        "--min_level",
        help="The level where generation starts",
        type=int,
        nargs="?",
        default=1,
    )
    parser.add_argument(
        "--max_level",
        help="The level where generation ends",
        type=int,
        nargs="?",
        default=1,
    )
    parser.add_argument(
        "--format",
        help="The format to write the RDF in. Options are xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, "
        "json-ld, hext",
        type=str,
        nargs="?",
        default="ttl",
    )
    args = parser.parse_args()
    Integrator(
        args.compressed,
        Path(args.path),
        args.output_path,
        args.tolerance,
        args.min_level,
        args.max_level,
        args.format,
    )
