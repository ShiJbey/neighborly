#!/usr/bin/env python3
# pylint: disable=W0614,W0401
"""Sample Neighborly Simulation.

"""

import argparse
import pathlib
import pstats
import random
from cProfile import Profile
from pstats import SortKey

from neighborly.config import LoggingConfig, SimulationConfig
from neighborly.plugins import default_content
from neighborly.simulation import Simulation


def get_args() -> argparse.Namespace:
    """Configure CLI argument parser and parse args.

    Returns
    -------
    argparse.Namespace
        parsed CLI arguments.
    """

    parser = argparse.ArgumentParser("Neighborly Sample Simulation.")

    parser.add_argument(
        "-s",
        "--seed",
        default=str(random.randint(0, 9999999)),
        type=str,
        help="The world seed.",
    )

    parser.add_argument(
        "-y",
        "--years",
        default=150,
        type=int,
        help="The number of years to simulate.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="Specify path to write generated JSON data.",
    )

    parser.add_argument(
        "-p",
        "--profiling",
        action="store_true",
        help="Enable profiling.",
    )

    parser.add_argument(
        "--disable-logging",
        help="Disable logging events to a file.",
        action="store_true",
    )

    parser.add_argument(
        "--profile-out",
        type=pathlib.Path,
        default=pathlib.Path("./profile.prof"),
        help="Specify path to write the profile data.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    from neighborly.inspection import *

    args = get_args()

    sim = Simulation(
        SimulationConfig(
            seed=args.seed,
            logging=LoggingConfig(
                logging_enabled=not bool(args.disable_logging),
                log_level="DEBUG",
                log_to_terminal=False,
            ),
        )
    )

    default_content.load_plugin(sim)

    if args.profiling:
        with Profile() as profile:
            sim.run_for(args.years)

            (
                pstats.Stats(profile)
                .strip_dirs()  # type: ignore
                .sort_stats(SortKey.PCALLS)
                .dump_stats(args.profile_out)
            )
    else:
        sim.run_for(args.years)

    if args.output:
        output_path: pathlib.Path = (
            args.output
            if args.output
            else pathlib.Path(__file__).parent / f"neighborly_{sim.config.seed}.json"
        )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(sim.to_json())

        print(f"Simulation output written to: {output_path}")
