"""
In this sample, I am adjusting the event system to be more ergonomic
"""
from dataclasses import dataclass
from pprint import pprint
import random
from typing import Dict, Any

from neighborly.core.ecs import GameObject, Component
from neighborly.core.life_event import (
    LifeEvent,
    event_precondition,
    event_effect,
    ILifeEventCallback,
)
from neighborly.core.relationship import RelationshipTag
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.character import (
    AgeRanges,
    CharacterDefinition,
    CharacterName,
    FamilyGenerationOptions,
    GameCharacter,
    GenerationConfig,
    LifeCycleConfig,
)
from neighborly.core.business import Occupation
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig

# ==============================
# HELPER PRECONDITION FUNCTIONS
# ==============================


def always_accept(gameobject: GameObject, event: LifeEvent) -> bool:
    """Event precondition function that always returns True"""
    return True


def reject(gameobject: GameObject, event: LifeEvent) -> bool:
    """Event precondition function that always returns False"""
    return True


def friendship_greater_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    friendship value for a character to another is greater than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return (
                relationship_net.get_connection(gameobject.id, other.id).friendship
                > value
            )
        return False

    return fn


def friendship_less_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    friendship value for a character to another is less than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return (
                relationship_net.get_connection(gameobject.id, other.id).friendship
                < value
            )
        return False

    return fn


def friendship_equal_to(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    friendship value for a character to another is equal to
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return (
                relationship_net.get_connection(gameobject.id, other.id).friendship
                == value
            )
        return False

    return fn


def romance_greater_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    romance value for a character to another is greater than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return (
                relationship_net.get_connection(gameobject.id, other.id).romance > value
            )
        return False

    return fn


def romance_less_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    romance value for a character to another is less than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return (
                relationship_net.get_connection(gameobject.id, other.id).romance < value
            )
        return False

    return fn


def romance_equal_to(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    romance value for a character to another is equal to
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return (
                relationship_net.get_connection(gameobject.id, other.id).romance
                == value
            )
        return False

    return fn


def relationship_has_tag(tag: str) -> ILifeEventCallback:
    """
    Return true if the relationship between this character and
    another has the given tag
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            return relationship_net.get_connection(gameobject.id, other.id).has_tags(
                RelationshipTag[tag]
            )
        return False

    return fn


def is_single(gameobject: GameObject, event: LifeEvent) -> bool:
    """Return True if this character has no relationships tagged as significant others"""
    relationship_net = gameobject.world.get_resource(RelationshipNetwork)
    significant_other_relationships = relationship_net.get_all_relationships_with_tags(
        gameobject.id, RelationshipTag.SignificantOther
    )
    return bool(significant_other_relationships)


def is_unemployed(gameobject: GameObject, event: LifeEvent) -> bool:
    """Returns True if this character does not have a job"""
    return not gameobject.has_component(Occupation)


def is_employed(gameobject: GameObject, event: LifeEvent) -> bool:
    """Returns True if this character has a job"""
    return gameobject.has_component(Occupation)


# ==============================
# HELPER EFFECT FUNCTIONS
# ==============================


def add_relationship_tag(tag: str) -> ILifeEventCallback:
    """Add the given tag from another character for the given character"""

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            relationship_net.get_connection(gameobject.id, other.id).add_tags(
                RelationshipTag[tag]
            )
        return True

    return fn


def remove_relationship_tag(tag: str) -> ILifeEventCallback:
    """Remove the given tag from another character for the given character"""

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        relationship_net = gameobject.world.get_resource(RelationshipNetwork)
        if relationship_net.has_connection(gameobject.id, other.id):
            relationship_net.get_connection(gameobject.id, other.id).remove_tags(
                RelationshipTag[tag]
            )
        return True

    return fn


@event_precondition("test")
def test_event_precondition(gameobject: GameObject, event: LifeEvent) -> bool:
    print("Running precondition")
    return True


@event_effect("test")
def test_event_effect(gameobject: GameObject, event: LifeEvent) -> bool:
    print(f"Running post effect: {event.data}")
    return True


BASE_CHARACTER_TYPE = CharacterDefinition(
    name="BaseCharacter",
    lifecycle=LifeCycleConfig(
        can_age=True,
        can_die=True,
        chance_of_death=0.6,
        romantic_feelings_age=13,
        marriageable_age=18,
        age_ranges=AgeRanges(
            child=(0, 10),
            teen=(11, 19),
            young_adult=(20, 29),
            adult=(30, 60),
            senior=(60, 85),
        ),
    ),
    generation=GenerationConfig(
        first_name="#first_name#",
        last_name="#last_name#",
        family=FamilyGenerationOptions(
            probability_spouse=0.5, probability_children=0.3, num_children=(0, 3)
        ),
    ),
)


DEFAULT_NEIGHBORLY_CONFIG = NeighborlyConfig(
    simulation=SimulationConfig(
        seed=random.randint(0, 999999),
        hours_per_timestep=6,
        start_date="0000-00-00T00:00.000z",
        end_date="0100-00-00T00:00.000z",
    ),
    plugins=["neighborly.plugins.default_plugin"],
)


@dataclass
class DemonSlayer(Component):
    breathing_style: tuple[str, ...]
    demons_slain: int
    power_level: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "breathing_style": self.breathing_style,
            "demons_slain": self.demons_slain,
            "power_level": self.power_level,
        }


def main():
    sim = Simulation(DEFAULT_NEIGHBORLY_CONFIG)

    delores_a = GameObject(
        components=[
            GameCharacter(
                CharacterDefinition(
                    **{**BASE_CHARACTER_TYPE.dict(), "name": "Android"}
                ),
                CharacterName("Delores", "Abernathy"),
                30,
                events={
                    "become-friends": {
                        "preconditions": [friendship_greater_than(0)],
                        "effects": [add_relationship_tag("Friend")],
                    },
                    "become-enemies": {
                        "preconditions": [reject],
                    },
                },
            ),
        ]
    )

    pprint(delores_a.to_dict())

    sim.world.add_gameobject(delores_a)

    kamado_t = GameObject(
        components=[
            GameCharacter(
                CharacterDefinition(**{**BASE_CHARACTER_TYPE.dict(), "name": "Human"}),
                CharacterName("Kamado", "Tanjiro"),
                13,
                events={
                    "become-friends": {
                        "preconditions": [friendship_greater_than(0)],
                        "effects": [add_relationship_tag("Friend")],
                    },
                    "become-enemies": {
                        "preconditions": [reject],
                    },
                },
            ),
            DemonSlayer(("sun", "water"), 0, 10),
        ],
    )

    pprint(kamado_t.to_dict())

    sim.world.add_gameobject(kamado_t)


if __name__ == "__main__":
    main()
