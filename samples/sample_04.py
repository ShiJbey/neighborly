import random
from typing import List, Tuple

from neighborly.core.builtin.statuses import BusinessOwner, Unemployed
from neighborly.core.business import Business
from neighborly.core.character import CharacterDefinition, CharacterName, GameCharacter
from neighborly.core.ecs import GameObject, ISystem, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence
from neighborly.core.rng import DefaultRNG
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid, Town
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.simulation import Simulation

TOTAL_CHARACTERS: int = 0


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
            )
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
    character.location = residence.gameobject.id
    residence.gameobject.get_component(Location).whitelist.add(character.gameobject.id)
    print(
        f"{str(character.name)}({character.gameobject.id}) moved into a new home ({residence.gameobject.id})"
    )


def create_random_business() -> GameObject:
    """Create new business gameobject"""
    ...


def open_business_event(probability: float) -> ISystem:
    """Character opens a business if a certain probability hits"""

    def fn(world: World, **kwargs) -> None:
        for _, character in world.get_component(GameCharacter):
            if random.random() < probability:
                if character.hometown is None:
                    continue

                if character.gameobject.has_component(BusinessOwner):
                    return

                if not town.layout.has_vacancy():
                    continue

                character.gameobject.add_component(BusinessOwner(0, "random business"))

                print(f"{str(character.name)} became a business owner")
                # business = create_random_business()

                # construct_business(town, business.get_component(Business))

    return fn


class SpawnResidentsSystem:
    __slots__ = "chance_spawn"

    def __init__(self, chance_spawn: float = 0.5) -> None:
        self.chance_spawn: float = chance_spawn

    def __call__(self, world: World, **kwargs) -> None:
        """Handles new characters moving into the town"""
        global TOTAL_CHARACTERS

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
            character = create_character(("Joe", "Character"), 25)
            purchase_residence(character.get_component(GameCharacter), residence)
            move_into_residence(character.get_component(GameCharacter), residence)


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
        residence = engine.create_residence(
            world, rng.choice(engine.get_residence_archetypes()).get_name()
        )

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
        unemployed_characters = list(
            map(lambda x: x[1], world.get_component(Unemployed))
        )

        for _, business in world.get_component(Business):
            # Skip businesses that don't need owners
            if not business.needs_owner():
                return


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

    sim.establish_setting(
        SimDateTime.from_iso_str("0000-00-00T00:00.000z"),
        SimDateTime.from_iso_str("0050-00-00T00:00.000z"),
    )

    print("Done")
    # sim.add_system(resident_immigration_system)
    # sim.add_system(open_business_event(1.0))
    # sim.ad

    #
    # sim.world.add_gameobject(town)
    #
    # for _ in range(10):
    #     sim.step()


if __name__ == "__main__":
    main()
