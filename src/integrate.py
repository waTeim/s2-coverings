from __future__ import annotations

import argparse

from lib.integrator import Integrator


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
        "--compressed",
        help="use the S2 hierarchy to write a compressed collection of relations at various levels",
        type=bool,
        nargs="?",
        default=True,
    )
    args = parser.parse_args()
    Integrator(args.compressed, args.path)
