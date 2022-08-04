from __future__ import annotations

import time
from typing import Dict, List, Optional, cast

from neighborly.builtin.helpers import move_residence
from neighborly.builtin.statuses import Adult, BusinessOwner, Dependent, Unemployed, Married
from neighborly.builtin.systems import BusinessSystem
from neighborly.core.behavior_tree import selector
from neighborly.core.business import (
    Business,
    Occupation,
    OccupationDefinition,
    BusinessArchetype, BusinessArchetypeLibrary
)
from neighborly.core.character import GameCharacter, CharacterArchetype, CharacterArchetypeLibrary
from neighborly.core.ecs import EntityArchetype, ISystem, World, GameObject
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    EventRoles,
    EventRoleType,
    LifeEvents,
    LifeEventType,
    LifeEvent, RoleFilterFn, LifeEventLog, EventRole
)
from neighborly.core.position import Position2D
from neighborly.core.relationship import RelationshipTag, RelationshipGraph
from neighborly.core.residence import Residence, Resident
from neighborly.core.routine import Routine
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid
from neighborly.plugins.default_plugin import (
    DefaultNameDataPlugin,
    DefaultResidencesPlugin, DefaultBusinessesPlugin,
)
from neighborly.simulation import Simulation, Plugin


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
                BusinessOwner(business.gameobject.id, business.name)
            )
            character.gameobject.remove_component(Unemployed)
            character.gameobject.add_component(
                Occupation(
                    OccupationDefinition.get_registered_type(
                        business.owner_type
                    ),
                    business.gameobject.id,
                )
            )
            business.owner = character.gameobject.id
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
                f"{str(character.name)} was hired as the owner of {business.name}({business.gameobject.id})"
            )


class FindEmployeesSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        unemployed_characters: List[GameCharacter] = list(
            map(lambda x: x[1][0], self.world.get_components(GameCharacter, Unemployed))
        )

        engine = self.world.get_resource(NeighborlyEngine)
        date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

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

                event_log.record_event(LifeEvent(
                    "HiredAtBusiness",
                    date.to_iso_str(),
                    roles=[
                        EventRole("Business", business.gameobject.id),
                        EventRole("Employee", character.gameobject.id)
                    ],
                    position=position
                ))


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


def over_age(age: int) -> RoleFilterFn:
    def fn(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        return gameobject.get_component(GameCharacter).age > age

    return fn


def single_person_role_type() -> EventRoleType:
    def can_get_married(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        if len(rel_graph.get_all_relationships_with_tags(gameobject.id, RelationshipTag.SignificantOther)):
            return False
        return True

    return EventRoleType("SinglePerson", [GameCharacter, Adult], filter_fn=can_get_married)


def potential_spouse_role() -> EventRoleType:
    def filter_fn(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        is_single = len(rel_graph.get_all_relationships_with_tags(gameobject.id, RelationshipTag.SignificantOther)) == 0
        in_love = rel_graph.get_connection(gameobject.id, event["SinglePerson"]).romance > 45
        return is_single and in_love

    return EventRoleType("PotentialSpouse", [GameCharacter, Adult], filter_fn=filter_fn)


def marriage_event() -> LifeEventType:
    def get_married(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)
        spouse1 = world.get_gameobject(event["SinglePerson"])
        spouse2 = world.get_gameobject(event["PotentialSpouse"])

        spouse2.get_component(GameCharacter).name.surname = spouse1.get_component(GameCharacter).name.surname

        spouse1.add_component(Married(
            partner_id=spouse2.id,
            partner_name=str(spouse2.get_component(GameCharacter).name)
        ))

        spouse2.add_component(Married(
            partner_id=spouse1.id,
            partner_name=str(spouse1.get_component(GameCharacter).name)
        ))

        rel_graph.get_connection(spouse1.id, spouse2.id).add_tags(
            RelationshipTag.Spouse | RelationshipTag.SignificantOther)
        rel_graph.get_connection(spouse2.id, spouse1.id).add_tags(
            RelationshipTag.Spouse | RelationshipTag.SignificantOther)

    return LifeEventType("Marriage", [EventRoles.get("SinglePerson"), EventRoles.get("PotentialSpouse")],
                         execute_fn=get_married)


def hiring_business_role() -> EventRoleType:
    """Defines a Role for a business with job opening"""

    def help_wanted(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        business = gameobject.get_component(Business)
        return len(business.get_open_positions()) > 0

    return EventRoleType("HiringBusiness", components=[Business], filter_fn=help_wanted)


def unemployed_role() -> EventRoleType:
    """Defines event Role for a character without a job"""
    return EventRoleType("Unemployed", components=[Unemployed])


def hire_employee_event() -> LifeEventType:
    def cb(world: World, event: LifeEvent):
        engine = world.get_resource(NeighborlyEngine)
        character = world.get_gameobject(event["Unemployed"]).get_component(GameCharacter)
        business = world.get_gameobject(event["HiringBusiness"]).get_component(Business)

        position = engine.rng.choice(business.get_open_positions())

        character.gameobject.remove_component(Unemployed)

        business.add_employee(character.gameobject.id, position)
        character.gameobject.add_component(
            Occupation(
                OccupationDefinition.get_registered_type(position),
                business.gameobject.id,
            )
        )

    return LifeEventType(
        "HiredAtBusiness",
        roles=[
            EventRoles.get("HiringBusiness"),
            EventRoles.get("Unemployed")
        ],
        execute_fn=cb
    )


class LifeEventPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        EventRoles.register("SinglePerson", single_person_role_type())
        EventRoles.register("PotentialSpouse", potential_spouse_role())
        EventRoles.register("HiringBusiness", hiring_business_role())
        EventRoles.register("Unemployed", unemployed_role())
        LifeEvents.register("HiredAtBusiness", hire_employee_event())
        LifeEvents.register("Marriage", marriage_event())

        # LifeEvents.register(
        #     "GreetOverlord",
        #     LifeEventType(
        #         "GreetOverlord",
        #         [EventRoles.get("Rando")],
        #         execute_fn=greet_overlord
        #     ),
        # )


def main():
    sim = (
        Simulation.create()
        .add_plugin(DefaultBusinessesPlugin())
        .add_plugin(DefaultNameDataPlugin())
        .add_plugin(DefaultResidencesPlugin())
        .add_system(FindBusinessOwnerSystem())
        .add_system(FindEmployeesSystem())
        .add_system(MoveOutOfParents())
        .add_system(BusinessSystem())
        .add_plugin(LifeEventPlugin())
    )

    CharacterArchetypeLibrary.register(CharacterArchetype(
        name="Person",
        name_format="#first_name# #family_name#",
        extra_components={
            Routine: {}
        },
        lifespan=85,
        life_stages={
            "child": 0,
            "teen": 13,
            "young_adult": 18,
            "adult": 30,
            "elder": 65,
        }
    ))

    BusinessArchetypeLibrary.register(BusinessArchetype(
        "Restaurant",
        name_format="#restaurant_name#",
        hours="Everyday 10:00 - 21:00",
        owner_type="Proprietor",
        employee_types={
            "Cook": 1,
            "Server": 2,
            "Host": 1,
        },
    ))

    sim.world.get_resource(LifeEventLog).subscribe(lambda e: print(str(e)))

    # get the start time
    st = time.time()
    sim.establish_setting()

    print(f"World Date: {sim.get_time().to_iso_str()}")

    elapsed_time = time.time() - st
    print('Execution time: ', elapsed_time, 'seconds')


if __name__ == "__main__":
    main()
