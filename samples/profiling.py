#!/usr/bin/env python3

"""Performance Profiling.

This module is for profiling the performance of a simulation.

"""

import argparse
import pathlib
import random
from cProfile import Profile
from pstats import SortKey, Stats

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
from neighborly.systems import PassiveReputationChange, PassiveRomanceChange

TEST_DATA_DIR = pathlib.Path(__file__).parent.parent / "tests" / "data"


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
        default=5,
        type=int,
        help="The number of years to simulate.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("./profile.prof"),
        help="Specify path to write generated world data.",
    )

    return parser.parse_args()


if __name__ == "__main__":

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

    sim.world.systems.get_system(PassiveReputationChange).set_active(False)
    sim.world.systems.get_system(PassiveRomanceChange).set_active(False)

    sim.initialize()

    with Profile() as profile:
        for _ in range(total_time_steps):
            sim.step()

        (Stats(profile).strip_dirs().sort_stats(SortKey.PCALLS).dump_stats(args.output))
