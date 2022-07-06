from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Type, TypeVar, Union

from neighborly.core.builtin.statuses import BusinessOwner, Unemployed
from neighborly.core.business import Business, Occupation
from neighborly.core.character import CharacterDefinition, CharacterName, GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.helpers import move_to_location
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import Routine
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid, Town
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.simulation import Simulation

_CT = TypeVar("_CT", bound=Component)


class EntityArchetype:
    """
    Organizes information for constructing components that compose GameObjects.

    Attributes
    ----------
    _name: str
        (Read-only) The name of the entity archetype
    _components: Dict[Type[_CT], Dict[str, Any]]
        Dict of components used to construct this archetype
    """

    __slots__ = "_name", "_components"

    def __init__(self, name: str) -> None:
        self._name: str = name
        self._components: Dict[Type[_CT], Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        """Returns the name of this archetype"""
        return self._name

    @property
    def components(self) -> Dict[Type[_CT], Dict[str, Any]]:
        """Returns a list of components in this archetype"""
        return {**self._components}

    def add(self, component_type: Union[Type[_CT], str], **kwargs) -> EntityArchetype:
        """
        Add a component to this archetype

        Parameters
        ----------
        component_type: subclass of neighborly.core.ecs.Component
            The component type to add to the entity archetype
        **kwargs: Dict[str, Any]
            Attribute overrides to pass to the component
        """
        self._components[component_type] = {**kwargs}
        return self

    def __repr__(self) -> str:
        return "{}(name={}, components={})".format(
            self.__class__.__name__, self._name, self._components
        )


@dataclass
class CharacterSpawnInfo:
    """Information used when spawning new characters into the simulation"""

    spawn_multiplier: int = 1


human_archetype = (
    EntityArchetype("Human").add(GameCharacter).add(Position2D, **{"x": 5, "y": 5})
)


def create_house(name: str) -> GameObject:
    return GameObject(
        components=[
            Location(8, name=name, is_private=True),
            Residence(),
        ]
    )


def create_character(name: Tuple[str, str], age: int) -> GameObject:
    character_name = CharacterName(name[0], name[1])

    return GameObject(
        components=[
            GameCharacter(
                CharacterDefinition(
                    **{
                        "definition_name": "Human",
                        "first_name_style": name[0],
                        "family_name_style": name[1],
                        "lifecycle": {
                            "lifespan": 86,
                            "life_stages": {
                                "child": 0,
                                "teen": 13,
                                "young_adult": 18,
                                "adult": 30,
                                "elder": 65,
                            },
                        },
                    }
                ),
                name=character_name,
                age=age,
            ),
            Routine(),
        ]
    )


def purchase_residence(character: GameCharacter, residence: Residence) -> None:
    """Have a one or more characters purchase a residence"""
    residence.add_owner(character.gameobject.id)
    print(
        f"{str(character.name)}({character.gameobject.id}) purchased a new home ({residence.gameobject.id})"
    )


def open_business(character: GameCharacter, business: Business) -> None:
    """Set the character as the owner and update their and the business' state"""
    business.hire_owner(character.gameobject.id)


def move_into_residence(character: GameCharacter, residence: Residence) -> None:
    """Move a character into a residence"""
    residence.add_resident(character.gameobject.id)
    character.location_aliases["home"] = residence.gameobject.id
    residence.gameobject.get_component(Location).whitelist.add(character.gameobject.id)
    print(
        f"{str(character.name)}({character.gameobject.id}) moved into a new home ({residence.gameobject.id})"
    )


class SpawnResidentsSystem:
    __slots__ = "chance_spawn"

    def __init__(self, chance_spawn: float = 0.5) -> None:
        self.chance_spawn: float = chance_spawn

    def __call__(self, world: World, **kwargs) -> None:
        """Handles new characters moving into the town"""
        rng = world.get_resource(DefaultRNG)
        engine = world.get_resource(NeighborlyEngine)

        for _, residence in world.get_component(Residence):
            # Skip occupied residences
            if not residence.is_vacant():
                continue

            # Return early if the random-roll is not sufficient
            if rng.random() > self.chance_spawn:
                return

            # Create a new character
            character = engine.spawn_character(world)
            purchase_residence(character.get_component(GameCharacter), residence)
            move_into_residence(character.get_component(GameCharacter), residence)
            move_to_location(
                world,
                character.get_component(GameCharacter),
                residence.gameobject.get_component(Location),
            )


class BuildResidenceSystem:

    __slots__ = "chance_of_build"

    def __init__(self, chance_of_build: float = 0.5) -> None:
        self.chance_of_build: float = chance_of_build

    def __call__(self, world: World, **kwargs) -> None:
        """Build a new residence when there is space"""
        rng = world.get_resource(DefaultRNG)
        land_grid = world.get_resource(LandGrid)
        engine = world.get_resource(NeighborlyEngine)

        # Return early if the random-roll is not sufficient
        if rng.random() > self.chance_of_build:
            return

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = rng.choice(land_grid.get_vacancies())

        # Construct a random residence archetype
        residence = engine.spawn_residence(world)

        # Reserve the space
        land_grid.reserve_space(lot, residence.id)

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))

        print(f"Built a new residence({residence.id}) at {lot}")


class BuildBusinessSystem:

    __slots__ = "chance_of_build"

    def __init__(self, chance_of_build: float = 0.5) -> None:
        self.chance_of_build: float = chance_of_build

    def __call__(self, world: World, **kwargs) -> None:
        """Build a new business when there is space"""
        rng = world.get_resource(DefaultRNG)
        land_grid = world.get_resource(LandGrid)
        engine = world.get_resource(NeighborlyEngine)

        # Return early if the random-roll is not sufficient
        if rng.random() > self.chance_of_build:
            return

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = rng.choice(land_grid.get_vacancies())

        # Build a random business archetype
        business = GameObject()
        world.add_gameobject(business)

        # Reserve the space
        land_grid.reserve_space(lot, business.id)

        # Set the position of the residence
        business.add_component(Position2D(lot[0], lot[1]))

        print(f"Built a new business({business.id}) at {lot}")


class FindBusinessOwnerSystem:
    def __call__(self, world: World, **kwargs) -> None:
        unemployed_characters: List[GameCharacter] = list(
            map(lambda x: x[1], world.get_component(Unemployed))
        )

        for _, business in world.get_component(Business):
            if not business.needs_owner():
                return

            character = world.get_resource(DefaultRNG).choice(unemployed_characters)
            character.gameobject.add_component(BusinessOwner(0, "random business"))
            character.gameobject.remove_component(Unemployed)
            # character.gameobject.add_component(Occupation())
            business.hire_owner(character.gameobject.id)


def main():
    sim = (
        Simulation.default()
        .add_plugin(DefaultPlugin())
        .add_system(BuildResidenceSystem())
        .add_system(SpawnResidentsSystem())
        .add_system(BuildBusinessSystem())
        .add_system(FindBusinessOwnerSystem())
        .create_land("small")
    )

    sim.get_engine().add_character_archetype(
        EntityArchetype("Human").add(GameCharacter)
    )

    sim.establish_setting(
        SimDateTime.from_iso_str("0000-00-00T00:00.000z"),
        SimDateTime.from_iso_str("0050-00-00T00:00.000z"),
    )

    print("Done")


if __name__ == "__main__":
    main()
