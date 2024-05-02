#!/usr/bin/env python3
# pylint: disable=W0614,W0401,W0621
"""Sample Simulation for Terminal.

"""

import argparse
import pathlib
import random

from neighborly.action import Action
from neighborly.components.business import Occupation
from neighborly.components.character import Character, LifeStage
from neighborly.config import LoggingConfig, SimulationConfig
from neighborly.libraries import ActionConsiderationLibrary
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
    load_skills,
    load_species,
)
from neighborly.plugins import (
    default_character_names,
    default_settlement_names,
    default_systems,
    default_traits,
)
from neighborly.plugins.actions import BecomeBusinessOwner
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
        default=150,
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


def has_occupation_consideration(action: Action) -> float:
    """Characters with occupations are not eligible to become business owners."""

    if isinstance(action, BecomeBusinessOwner):
        if action.character.has_component(Occupation):
            return 0

    return -1


def life_stage_consideration(action: Action) -> float:
    """Characters with occupations are not eligible to become business owners."""

    if isinstance(action, BecomeBusinessOwner):
        life_stage = action.character.get_component(Character).life_stage

        if life_stage < LifeStage.ADULT:
            return 0

        if life_stage < LifeStage.SENIOR:
            return 0.5

        # Seniors
        return 0.3

    return -1


def main() -> Simulation:
    """Main program entry point."""
    args = get_args()

    sim = Simulation(
        SimulationConfig(
            seed=args.seed,
            settlement="basic_settlement",
            logging=LoggingConfig(logging_enabled=True),
        )
    )

    load_districts(sim, TEST_DATA_DIR / "districts.json")
    load_settlements(sim, TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, TEST_DATA_DIR / "businesses.json")
    load_characters(sim, TEST_DATA_DIR / "characters.json")
    load_residences(sim, TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, TEST_DATA_DIR / "job_roles.json")
    load_skills(sim, TEST_DATA_DIR / "skills.json")
    load_species(sim, TEST_DATA_DIR / "species.json")

    default_traits.load_plugin(sim)
    default_character_names.load_plugin(sim)
    default_settlement_names.load_plugin(sim)
    default_systems.load_plugin(sim)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_utility_consideration("become-business-owner", lambda action: 0.5)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("become-business-owner", has_occupation_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("become-business-owner", life_stage_consideration)

    total_time_steps: int = args.years * 12

    sim.initialize()

    for _ in range(total_time_steps):
        sim.step()

    if args.output:
        output_path: pathlib.Path = (
            args.output
            if args.output
            else pathlib.Path(__file__).parent / f"neighborly_{sim.config.seed}.json"
        )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(sim.to_json())

        print(f"Simulation output written to: {output_path}")

    return sim


if __name__ == "__main__":
    from neighborly.inspection import *

    sim = main()
