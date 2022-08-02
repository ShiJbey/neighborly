from __future__ import annotations

import random
from typing import Dict, List, Optional, cast

from neighborly.core.behavior_tree import selector
from neighborly.core.builtin.statuses import Adult, BusinessOwner, Dependent, Unemployed
from neighborly.core.business import (
    Business,
    BusinessStatus,
    Occupation,
    OccupationDefinition,
)
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import EntityArchetype, ISystem, World, GameObject
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.helpers import move_to_location
from neighborly.core.life_event import (
    EventRoleDatabase,
    EventRoleType,
    LifeEventDatabase,
    LifeEventType,
    LifeEventSimulator, LifeEvent
)
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence, Resident
from neighborly.core.routine import Routine
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
from neighborly.core.town import LandGrid, Town
from neighborly.plugins.default_plugin import (
    DefaultBusinessesPlugin,
    DefaultNameDataPlugin,
    DefaultPlugin,
    DefaultResidencesPlugin,
)
from neighborly.simulation import Simulation, Plugin


def purchase_residence(character: GameCharacter, residence: Residence) -> None:
    """Have a one or more characters purchase a residence"""
    residence.add_owner(character.gameobject.id)
    print(
        f"{str(character.name)}({character.gameobject.id}) purchased a new home ({residence.gameobject.id})"
    )

    # world = character.gameobject.world

    # character.gameobject.handle_event(
    #     HomePurchaseEvent(
    #         timestamp=world.get_resource(SimDateTime).to_iso_str(),
    #         residence_id=residence.gameobject.id,
    #         character_id=character.gameobject.id,
    #         character_name=str(character.name),
    #     )
    # )


def move_residence(character: GameCharacter, residence: Residence) -> None:
    """Move a character into a residence"""

    world = character.gameobject.world

    # Move out of the old residence
    if "home" in character.location_aliases:
        old_residence = world.get_gameobject(
            character.location_aliases["home"]
        ).get_component(Residence)
        old_residence.remove_resident(character.gameobject.id)
        if old_residence.is_owner(character.gameobject.id):
            old_residence.remove_owner(character.gameobject.id)
        old_residence.gameobject.get_component(Location).whitelist.remove(
            character.gameobject.id
        )

    # Move into new residence
    residence.add_resident(character.gameobject.id)
    character.location_aliases["home"] = residence.gameobject.id
    residence.gameobject.get_component(Location).whitelist.add(character.gameobject.id)
    character.gameobject.add_component(Resident(residence.gameobject.id))
    # character.gameobject.handle_event(
    #     MoveResidenceEvent(
    #         timestamp=world.get_resource(SimDateTime).to_iso_str(),
    #         residence_id=residence.gameobject.id,
    #         character_id=character.gameobject.id,
    #         character_name=str(character.name),
    #     )
    # )

    print(
        f"{str(character.name)}({character.gameobject.id}) moved into a new home ({residence.gameobject.id})"
    )


class SpawnResidentsSystem(ISystem):
    __slots__ = "chance_spawn"

    def __init__(self, chance_spawn: float = 0.5) -> None:
        super().__init__()
        self.chance_spawn: float = chance_spawn

    def process(self, *args, **kwargs) -> None:
        """Handles new characters moving into the town"""
        engine = self.world.get_resource(NeighborlyEngine)
        town = self.world.get_resource(Town)

        for _, residence in self.world.get_component(Residence):
            # Skip occupied residences
            if not residence.is_vacant():
                continue

            # Return early if the random-roll is not sufficient
            if engine.rng.random() > self.chance_spawn:
                return

            # Create a new character
            character = engine.spawn_character(self.world)
            character.add_component(Unemployed())

            purchase_residence(character.get_component(GameCharacter), residence)
            move_residence(character.get_component(GameCharacter), residence)
            move_to_location(
                self.world,
                character.get_component(GameCharacter),
                residence.gameobject.get_component(Location),
            )

            town.population += 1


class BuildResidenceSystem(ISystem):
    __slots__ = "chance_of_build"

    def __init__(self, chance_of_build: float = 0.5) -> None:
        super().__init__()
        self.chance_of_build: float = chance_of_build

    def process(self, *args, **kwargs) -> None:
        """Build a new residence when there is space"""
        land_grid = self.world.get_resource(LandGrid)
        engine = self.world.get_resource(NeighborlyEngine)

        # Return early if the random-roll is not sufficient
        if engine.rng.random() > self.chance_of_build:
            return

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(land_grid.get_vacancies())

        # Construct a random residence archetype
        residence = engine.spawn_residence(self.world)

        if residence is None:
            return

        # Reserve the space
        land_grid.reserve_space(lot, residence.id)

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))

        print(f"Built a new Residence({residence.id}) at {lot}")


class BuildBusinessSystem(ISystem):
    __slots__ = "chance_of_build"

    def __init__(self, chance_of_build: float = 0.5) -> None:
        super().__init__()
        self.chance_of_build: float = chance_of_build

    def process(self, *args, **kwargs) -> None:
        """Build a new business when there is space"""
        land_grid = self.world.get_resource(LandGrid)
        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)

        # Return early if the random-roll is not sufficient
        if engine.rng.random() > self.chance_of_build:
            return

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(land_grid.get_vacancies())

        # Build a random business archetype
        business = engine.spawn_business(self.world, population=town.population)

        if business is None:
            return

        # Reserve the space
        land_grid.reserve_space(lot, business.id)

        # Set the position of the residence
        business.add_component(Position2D(lot[0], lot[1]))

        print(
            f"Built a new {business.get_component(Business).get_type().name}({business.id}), "
            f"'{business.get_component(Business).get_name()}', at {lot}"
        )


class FindBusinessOwnerSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        unemployed_characters: List[GameCharacter] = list(
            map(lambda x: x[1][0], self.world.get_components(GameCharacter, Unemployed))
        )

        engine = self.world.get_resource(NeighborlyEngine)

        for _, business in self.world.get_component(Business):
            if not business.needs_owner():
                continue

            if len(unemployed_characters) == 0:
                break

            character = engine.rng.choice(unemployed_characters)
            character.gameobject.add_component(
                BusinessOwner(business.gameobject.id, business.get_name())
            )
            character.gameobject.remove_component(Unemployed)
            character.gameobject.add_component(
                Occupation(
                    OccupationDefinition.get_registered_type(
                        business.get_type().owner_type
                    ),
                    business.gameobject.id,
                )
            )
            business.set_owner(character.gameobject.id)
            unemployed_characters.remove(character)

            # character.gameobject.handle_event(
            #     JobHiringEvent(
            #         timestamp=world.get_resource(SimDateTime).to_iso_str(),
            #         business_id=business.gameobject.id,
            #         character_id=character.gameobject.id,
            #         character_name=str(character.name),
            #         business_name=business.get_name(),
            #         occupation_name=business.get_type().owner_type,
            #     )
            # )

            print(
                f"{str(character.name)} was hired as the owner of {business.get_name()}({business.gameobject.id})"
            )


class FindEmployeesSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        unemployed_characters: List[GameCharacter] = list(
            map(lambda x: x[1][0], self.world.get_components(GameCharacter, Unemployed))
        )

        engine = self.world.get_resource(NeighborlyEngine)

        for _, business in self.world.get_component(Business):
            open_positions = business.get_open_positions()

            for position in open_positions:
                if len(unemployed_characters) == 0:
                    break
                character = engine.rng.choice(unemployed_characters)
                character.gameobject.remove_component(Unemployed)

                business.add_employee(character.gameobject.id, position)
                character.gameobject.add_component(
                    Occupation(
                        OccupationDefinition.get_registered_type(position),
                        business.gameobject.id,
                    )
                )
                unemployed_characters.remove(character)

                # character.gameobject.handle_event(
                #     JobHiringEvent(
                #         timestamp=world.get_resource(SimDateTime).to_iso_str(),
                #         business_id=business.gameobject.id,
                #         character_id=character.gameobject.id,
                #         character_name=str(character.name),
                #         business_name=business.get_name(),
                #         occupation_name=position,
                #     )
                # )

                print(
                    f"{str(character.name)} was hired as a(n) {position} at {business.get_name()}({business.gameobject.id})"
                )


# class GetMarriedBehavior:
#     def check_preconditions(self, gameobject: GameObject) -> bool:
#         return (
#             gameobject.has_component(Adult)
#             and gameobject.has_component(Occupation)
#             and gameobject.has_component(Dependent)
#         )
#
#     def run(self, gameobject: GameObject) -> None:
#         world = gameobject.world
#         character = gameobject.get_component(GameCharacter)
#         resident = gameobject.get_component(Resident)
#         residence = world.get_gameobject(resident.residence).get_component(Residence)
#
#         if not residence.is_owner(character.gameobject.id):
#             vacant_residence = self.find_vacant_residence(world)
#             if vacant_residence:
#                 move_residence(character, vacant_residence)
#                 return
#
#             new_residence = self.build_new_residence(world)
#             if new_residence:
#                 move_residence(character, new_residence)
#                 return
#
#             # No residence found leave the simulation
#             # character.gameobject.handle_event(
#             #     DepartureEvent(
#             #         timestamp=world.get_resource(SimDateTime).to_iso_str(),
#             #         character_id=character.gameobject.id,
#             #         character_name=str(character.name),
#             #     )
#             # )


class MoveOutOfParents(ISystem):
    def process(self, *args, **kwargs) -> None:
        for _, (character, _, resident, _, _) in self.world.get_components(
            GameCharacter, Adult, Resident, Occupation, Dependent
        ):
            character = cast(GameCharacter, character)
            resident = cast(Resident, resident)
            residence = self.world.get_gameobject(resident.residence).get_component(
                Residence
            )

            if not residence.is_owner(character.gameobject.id):
                vacant_residence = self.find_vacant_residence(self.world)
                if vacant_residence:
                    move_residence(character, vacant_residence)
                    continue

                new_residence = self.build_new_residence(self.world)
                if new_residence:
                    move_residence(character, new_residence)
                    continue

                # No residence found leave the simulation
                # character.gameobject.handle_event(
                #     DepartureEvent(
                #         timestamp=world.get_resource(SimDateTime).to_iso_str(),
                #         character_id=character.gameobject.id,
                #         character_name=str(character.name),
                #     )
                # )

    def find_vacant_residence(self, world: World) -> Optional[Residence]:
        engine = world.get_resource(NeighborlyEngine)
        vacant_residences = list(
            filter(
                lambda r: r.is_vacant(),
                map(lambda _, r: r.is_vacant(), world.get_component(Residence)),
            )
        )
        if vacant_residences:
            return engine.rng.choice(vacant_residences)
        else:
            return None

    def build_new_residence(self, world: World) -> Optional[Residence]:
        land_grid = world.get_resource(LandGrid)
        engine = world.get_resource(NeighborlyEngine)

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(land_grid.get_vacancies())

        # Construct a random residence archetype
        residence = engine.spawn_residence(world)

        if residence is None:
            return

        # Reserve the space
        land_grid.reserve_space(lot, residence.id)

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))

        print(f"Built a new Residence ({residence.id}) at {lot}")

        return residence.get_component(Residence)


class BusinessSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        time = self.world.get_resource(SimDateTime)
        rng = self.world.get_resource(random.Random)
        for _, business in self.world.get_component(Business):
            if business.status == BusinessStatus.OpenForBusiness:
                # Increment the age of the business
                business.increment_years_in_business(time.delta_time / HOURS_PER_YEAR)

                # Check if this business is going to close
                if rng.random() < 0.3:
                    # Go Out of business
                    business.set_business_status(BusinessStatus.ClosedForBusiness)
                    business.set_owner(None)
                    for employee in business.get_employees():
                        business.remove_employee(employee)
                        self.world.get_gameobject(employee).remove_component(Occupation)


def create_character_archetype(
    archetype_name: str,
    first_name: str = "#first_name#",
    family_name: str = "#family_name#",
    life_stages: Optional[Dict[str, int]] = None,
    lifespan: int = 86,
) -> EntityArchetype:
    life_stages_default = {
        "child": 0,
        "teen": 13,
        "young_adult": 18,
        "adult": 30,
        "elder": 65,
    }

    overwritten_life_stages = (
        {**life_stages_default, **life_stages}
        if life_stages
        else {**life_stages_default}
    )

    return EntityArchetype(archetype_name).add(
        GameCharacter,
        type_name=archetype_name,
        first_name=first_name,
        family_name=family_name,
        aging={
            "lifespan": lifespan,
            "life_stages": overwritten_life_stages,
        },
    )


def say_hi(world: World, event: LifeEvent) -> bool:
    if world.get_resource(NeighborlyEngine).rng.random() < 0.5:
        character = world.get_gameobject(event["Rando"]).get_component(GameCharacter)
        print("{} says hello Overlord".format(str(character.name)))
        return True
    return False


def say_kiss_my_ass(world: World, event: LifeEvent) -> bool:
    if world.get_resource(NeighborlyEngine).rng.random() < 0.5:
        character = world.get_gameobject(event["Rando"]).get_component(GameCharacter)
        print("{} says kiss my ass Overlord".format(str(character.name)))
        return True
    return False


def greet_overlord(world: World, event: LifeEvent):
    selector(
        say_hi,
        say_kiss_my_ass
    )(world, event)


def over_age(age: int):
    def fn(event: LifeEvent, gameobject: GameObject) -> bool:
        return gameobject.get_component(GameCharacter).age > age

    return fn


class LifeEventPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        EventRoleDatabase.register(
            "Parent", EventRoleType("Parent", components=[GameCharacter])
        )

        EventRoleDatabase.register("Child", EventRoleType("Child", components=[GameCharacter]))

        EventRoleDatabase.register("Rando",
                                   EventRoleType("Rando", components=[GameCharacter], filter_fn=over_age(60)))

        # LifeEventDatabase.register(
        #     "Child-Birth",
        #     LifeEventType(
        #         "Child-Birth",
        #         [
        #             EventRoleDatabase.get("Child"),
        #             EventRoleDatabase.get("Parent"),
        #             EventRoleDatabase.get("Parent"),
        #         ],
        #         effect_fn=say_hi
        #     ),
        # )

        LifeEventDatabase.register(
            "GreetOverlord",
            LifeEventType(
                "GreetOverlord",
                [EventRoleDatabase.get("Rando")],
                effect_fn=greet_overlord
            ),
        )

        sim.add_system(LifeEventSimulator())


def main():
    sim = (
        Simulation.create()
        .add_plugin(DefaultPlugin())
        .add_resource(random.Random())
        .add_plugin(DefaultBusinessesPlugin())
        .add_plugin(DefaultNameDataPlugin())
        .add_plugin(DefaultResidencesPlugin())
        .add_system(BuildResidenceSystem())
        .add_system(SpawnResidentsSystem())
        .add_system(BuildBusinessSystem(0.2))
        .add_system(FindBusinessOwnerSystem())
        .add_system(FindEmployeesSystem())
        .add_system(MoveOutOfParents())
        .add_system(BusinessSystem())
        .add_plugin(LifeEventPlugin())
    )

    sim.get_engine().add_character_archetype(
        create_character_archetype("Human").add(Routine)
    )

    sim.get_engine().add_business_archetype(
        EntityArchetype("Restaurant").add(
            Business,
            business_type="Restaurant",
            name_format="#restaurant_name#",
            hours="Everyday 10:00 - 21:00",
            owner_type="Proprietor",
            employees={
                "Cook": 1,
                "Server": 2,
                "Host": 1,
            },
        )
    )

    sim.establish_setting()

    print(sim.get_time().to_iso_str())


if __name__ == "__main__":
    main()