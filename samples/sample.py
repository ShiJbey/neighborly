#!/usr/bin/env python3
# pylint: disable=W0614,W0401,W0621
"""Sample Simulation for Terminal.

"""

import argparse
import pathlib
import pstats
import random
from cProfile import Profile
from pstats import SortKey

import tqdm

from neighborly.action import Action
from neighborly.components.business import Business, Occupation
from neighborly.components.character import Character, LifeStage
from neighborly.components.relationship import Reputation, Romance
from neighborly.components.stats import Fertility
from neighborly.config import LoggingConfig, SimulationConfig
from neighborly.ecs import GameObject, IEvent
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.traits import get_relationships_with_traits, get_time_with_trait
from neighborly.libraries import ActionConsiderationLibrary
from neighborly.plugins import default_content
from neighborly.plugins.actions import (
    BecomeBusinessOwner,
    Divorce,
    FireEmployee,
    FormCrush,
    GetMarried,
    GetPregnant,
    Retire,
    StartDating,
)
from neighborly.plugins.default_events import DatingBreakUpEvent, DivorceEvent
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


def romance_consideration(action: Action) -> float:
    """Characters with occupations are not eligible to become business owners."""

    if isinstance(action, StartDating):
        outgoing_relationship = get_relationship(action.character, action.partner)
        outgoing_romance_stat = outgoing_relationship.get_component(Romance).stat.value
        if outgoing_romance_stat <= 0:
            return 0

        incoming_relationship = get_relationship(action.partner, action.character)
        incoming_romance_stat = incoming_relationship.get_component(Romance).stat.value
        if incoming_romance_stat <= 0:
            return 0

        romance_diff = abs(outgoing_romance_stat - incoming_romance_stat)

        if romance_diff < 10:
            return 0.8
        if romance_diff < 20:
            return 0.7
        if romance_diff < 30:
            return 0.6

    return -1


def is_single(character: GameObject) -> bool:
    """Return True if the character is not in a romantic relationship."""

    if get_relationships_with_traits(character, "dating"):
        return False

    if get_relationships_with_traits(character, "spouse"):
        return False

    return True


def existing_relationship_cons(action: Action) -> float:
    """Characters in relationships don't start dating or marriages with others."""

    if isinstance(action, StartDating):
        if not is_single(action.character):
            return 0.0

        if not is_single(action.character):
            return 0.0

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

        return normalized_reputation

    return -1


def fertility_consideration(action: Action) -> float:
    """Consider romance from a character to their potential crush."""
    if isinstance(action, GetPregnant):
        character_fertility = action.character.get_component(Fertility).stat.value
        partner_fertility = action.partner.get_component(Fertility).stat.value

        avg_fertility = (character_fertility + partner_fertility) / 2.0

        return avg_fertility / 100.0

    return -1


def marriage_time_dating_consideration(action: Action) -> float:
    """Consider how long you have been dating before getting married."""

    if isinstance(action, GetMarried):
        relationship = get_relationship(action.character, action.partner)
        months_dating = get_time_with_trait(relationship, "dating")
        years_dating = float(months_dating) / 12.0

        if months_dating == 0:
            return 0

        if years_dating > 3:
            return 0.9
        elif years_dating > 2:
            return 0.7
        elif years_dating > 1:
            return 0.5
        else:
            return 0.05

    return -1


def marriage_romance_consideration(action: Action) -> float:
    """Consider romantic feeling for marriage."""

    if isinstance(action, GetMarried):
        relationship = get_relationship(action.character, action.partner)
        romance = relationship.get_component(Romance).stat.normalized

        return romance**2

    return -1


def breakup_romance_consideration(action: Action) -> float:
    """Consider romantic feeling for break-up."""

    if isinstance(action, GetMarried):
        relationship = get_relationship(action.character, action.partner)
        romance = relationship.get_component(Romance).stat.normalized

        return 1 - romance**2

    return -1


def divorce_romance_consideration(action: Action) -> float:
    """Consider romantic feelings before divorce."""
    if isinstance(action, GetMarried):
        relationship = get_relationship(action.character, action.partner)
        romance = relationship.get_component(Romance).stat.normalized

        return 1 - (romance**2)

    return -1


def divorce_time_married_consideration(action: Action) -> float:
    """Consider how long you have been married before divorce."""

    if isinstance(action, Divorce):
        relationship = get_relationship(action.character, action.partner)
        months_married = get_time_with_trait(relationship, "spouse")
        years_married = float(months_married) / 12.0

        if months_married == 0:
            return 0

        if years_married > 30:
            return 0.1
        elif years_married > 20:
            return 0.2
        elif years_married > 10:
            return 0.4
        else:
            return 0.3

    return -1


def break_up_response(event: IEvent) -> None:
    """Listens for break ups and updates relationships."""

    if isinstance(event, DatingBreakUpEvent):

        get_relationship(event.partner, event.initiator).get_component(
            Romance
        ).stat.base_value -= 15
        get_relationship(event.partner, event.initiator).get_component(
            Reputation
        ).stat.base_value -= 15


def divorce_response(event: IEvent) -> None:
    """Listens for divorces and updates relationships."""

    if isinstance(event, DivorceEvent):

        get_relationship(event.partner, event.initiator).get_component(
            Romance
        ).stat.base_value -= 20
        get_relationship(event.partner, event.initiator).get_component(
            Reputation
        ).stat.base_value -= 25


def main() -> Simulation:
    """Main program entry point."""
    args = get_args()

    sim = Simulation(
        SimulationConfig(
            seed=args.seed,
            settlement="basic_settlement",
            logging=LoggingConfig(
                logging_enabled=not bool(args.disable_logging),
                log_level="DEBUG",
                log_to_terminal=False,
            ),
        )
    )

    default_content.load_plugin(sim)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("become-business-owner", lambda action: 0.5)
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
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("start-dating", existing_relationship_cons)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("get-pregnant", fertility_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("get-married", marriage_time_dating_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("divorce", divorce_time_married_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("get-married", marriage_romance_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("divorce", divorce_romance_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("break-up", breakup_romance_consideration)
    sim.world.events.on_event("dating_break_up", break_up_response)
    sim.world.events.on_event("divorce", divorce_response)

    total_time_steps: int = args.years * 12

    sim.initialize()

    if sim.config.logging.log_to_terminal:
        if args.profiling:
            with Profile() as profile:
                for _ in range(total_time_steps):
                    sim.step()

                (
                    pstats.Stats(profile)
                    .strip_dirs()  # type: ignore
                    .sort_stats(SortKey.PCALLS)
                    .dump_stats(args.profile_out)
                )
        else:
            for _ in range(total_time_steps):
                sim.step()
    else:
        if args.profiling:
            with Profile() as profile:
                for _ in tqdm.trange(total_time_steps):
                    sim.step()

                (
                    pstats.Stats(profile)
                    .strip_dirs()  # type: ignore
                    .sort_stats(SortKey.PCALLS)
                    .dump_stats(args.profile_out)
                )
        else:
            for _ in tqdm.trange(total_time_steps):
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
