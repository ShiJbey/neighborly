#!/usr/bin/env python3
# pylint: disable=W0614,W0401,W0621
"""Sample Simulation for Terminal.

"""

import argparse
import pathlib
import random

from neighborly.action import Action
from neighborly.components.business import Business, Occupation
from neighborly.components.character import Character, LifeStage
from neighborly.components.relationship import Reputation, Romance
from neighborly.config import LoggingConfig, SimulationConfig
from neighborly.helpers.relationship import get_relationship
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
from neighborly.plugins.actions import (
    BecomeBusinessOwner,
    FireEmployee,
    FormCrush,
    Retire,
    StartDating,
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


def romance_consideration(action: Action) -> float:
    """Characters with occupations are not eligible to become business owners."""

    if isinstance(action, StartDating):
        outgoing_relationship = get_relationship(action.character, action.partner)
        outgoing_romance_stat = outgoing_relationship.get_component(Romance).stat.value
        if outgoing_romance_stat <= 50:
            return 0

        incoming_relationship = get_relationship(action.partner, action.character)
        incoming_romance_stat = incoming_relationship.get_component(Romance).stat.value
        if incoming_romance_stat <= 50:
            return 0

        romance_diff = abs(outgoing_romance_stat - incoming_romance_stat)

        if romance_diff < 10:
            return 0.8
        if romance_diff < 20:
            return 0.7
        if romance_diff < 30:
            return 0.6

    return -1


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


def retirement_life_stage_cons(action: Action) -> float:
    """Senior characters are the only ones eligible to retire."""
    if isinstance(action, Retire):
        life_stage = action.character.get_component(Character).life_stage

        if life_stage == LifeStage.ADULT:
            return 0.05

        if life_stage == LifeStage.SENIOR:
            return 0.8

        # Everyone who is a young-adult or younger
        return 0.0

    return -1


def firing_owner_relationship_cons(action: Action) -> float:
    """Consider relationship of the owner to the potentially fired character."""
    if isinstance(action, FireEmployee):
        employee = action.character
        owner = action.business.get_component(Business).owner

        if owner is None:
            return -1

        relationship = get_relationship(owner, employee)

        normalized_reputation = relationship.get_component(Reputation).stat.normalized

        return 1 - (normalized_reputation**2)

    return -1


def crush_romance_consideration(action: Action) -> float:
    """Consider romance from a character to their potential crush."""
    if isinstance(action, FormCrush):
        relationship = get_relationship(action.character, action.crush)

        normalized_reputation = relationship.get_component(Reputation).stat.normalized

        return normalized_reputation**2

    return -1


def main() -> Simulation:
    """Main program entry point."""
    args = get_args()

    sim = Simulation(
        SimulationConfig(
            seed=args.seed,
            settlement="basic_settlement",
            logging=LoggingConfig(
                logging_enabled=True, log_level="DEBUG", log_to_terminal=False
            ),
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
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("start-dating", romance_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("fire-employee", firing_owner_relationship_cons)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("form-crush", crush_romance_consideration)

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
