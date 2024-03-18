#!/usr/bin/env python3
# pylint: disable=W0401,W0614

"""Sample Simulation for Terminal.

"""

import argparse
import pathlib
import random

from neighborly.config import LoggingConfig, SimulationConfig
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
    load_skills,
)
from neighborly.plugins import (
    default_character_names,
    default_settlement_names,
    default_traits,
)
from neighborly.simulation import Simulation

TEST_DATA_DIR = pathlib.Path(__file__).parent.parent / "tests" / "data"


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
        default=50,
        type=int,
        help="The number of years to simulate.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="Specify path to write generated world data.",
    )

    return parser.parse_args()


def main() -> Simulation:
    """Main program entry point."""
    args = get_args()

    _sim = Simulation(
        SimulationConfig(
            seed=args.seed,
            settlement_with_id="basic_settlement",
            logging=LoggingConfig(logging_enabled=True),
        )
    )

    load_districts(_sim, TEST_DATA_DIR / "districts.json")
    load_settlements(_sim, TEST_DATA_DIR / "settlements.json")
    load_businesses(_sim, TEST_DATA_DIR / "businesses.json")
    load_characters(_sim, TEST_DATA_DIR / "characters.json")
    load_residences(_sim, TEST_DATA_DIR / "residences.json")
    load_job_roles(_sim, TEST_DATA_DIR / "job_roles.json")
    load_skills(_sim, TEST_DATA_DIR / "skills.json")

    # default_events.load_plugin(_sim)
    default_traits.load_plugin(_sim)
    default_character_names.load_plugin(_sim)
    default_settlement_names.load_plugin(_sim)

    total_time_steps: int = args.years * 12

    for _ in range(total_time_steps):
        _sim.step()

    if args.output:
        output_path: pathlib.Path = (
            args.output
            if args.output
            else pathlib.Path(__file__).parent / f"neighborly_{_sim.config.seed}.json"
        )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(_sim.to_json())

        print(f"Simulation output written to: {output_path}")

    return _sim


if __name__ == "__main__":
    from neighborly.inspection import *

    sim = main()
