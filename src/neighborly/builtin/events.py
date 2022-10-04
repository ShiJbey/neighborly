from __future__ import annotations

from typing import List, Optional, cast

from neighborly.builtin.helpers import move_residence
from neighborly.builtin.role_filters import is_single
from neighborly.builtin.statuses import (
    Adult,
    Dating,
    Deceased,
    Elder,
    Married,
    Pregnant,
    Present,
    Retired,
)
from neighborly.core.business import Occupation, Unemployed
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    LifeEvent,
    LifeEventLog,
    LifeEventType,
    RoleType,
    join_filters, constant_probability,
)
from neighborly.core.relationship import RelationshipGraph, RelationshipTag
from neighborly.core.residence import Residence, Resident
from neighborly.core.time import SimDateTime


def become_friends_event(
    threshold: int = 25, probability: float = 1.0
) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def bind_potential_friend(world: World, event: LifeEvent):
        """
        Return a Character that has a mutual friendship score
        with PersonA that is above a given threshold
        """
        rel_graph = world.get_resource(RelationshipGraph)
        engine = world.get_resource(NeighborlyEngine)
        person_a_relationships = rel_graph.get_relationships(event["PersonA"])
        eligible_characters: List[GameObject] = []
        for rel in person_a_relationships:
            other_character = world.get_gameobject(rel.target)
            if (
                other_character.has_component(Present)
                and rel_graph.has_connection(rel.target, event["PersonA"])
                and (
                rel_graph.get_connection(rel.target, event["PersonA"]).friendship
                >= threshold
            )
                and not rel_graph.get_connection(rel.target, event["PersonA"]).has_tags(
                RelationshipTag.Friend
            )
                and not rel.has_tags(RelationshipTag.Friend)
                and rel.friendship >= threshold
            ):
                eligible_characters.append(other_character)

        if eligible_characters:
            return engine.rng.choice(eligible_characters)
        return None

    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)
        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.Friend
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.Friend
        )
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="BecomeFriends",
        roles=[
            RoleType(name="PersonA", components=[GameCharacter, Present]),
            RoleType(name="PersonB", binder_fn=bind_potential_friend),
        ],
        effects=execute,
        probability=constant_probability(probability),
    )


def become_enemies_event(
    threshold: int = -25, probability: float = 1.0
) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def bind_potential_enemy(world: World, event: LifeEvent):
        """
        Return a Character that has a mutual friendship score
        with PersonA that is above a given threshold
        """
        rel_graph = world.get_resource(RelationshipGraph)
        engine = world.get_resource(NeighborlyEngine)
        person_a_relationships = rel_graph.get_relationships(event["PersonA"])
        eligible_characters: List[GameObject] = []
        for rel in person_a_relationships:
            if (
                world.has_gameobject(rel.target)
                and rel_graph.has_connection(rel.target, event["PersonA"])
                and (
                rel_graph.get_connection(rel.target, event["PersonA"]).friendship
                <= threshold
            )
                and not rel_graph.get_connection(rel.target, event["PersonA"]).has_tags(
                RelationshipTag.Friend
            )
                and not rel.has_tags(RelationshipTag.Friend)
                and rel.friendship <= threshold
            ):
                eligible_characters.append(world.get_gameobject(rel.target))

        if eligible_characters:
            return engine.rng.choice(eligible_characters)
        return None

    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)
        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.Enemy
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.Enemy
        )
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="BecomeEnemies",
        roles=[
            RoleType(name="PersonA", components=[GameCharacter]),
            RoleType(
                name="PersonB",
                binder_fn=bind_potential_enemy,
            ),
        ],
        effects=execute,
        probability=constant_probability(probability),
    )


def start_dating_event(threshold: int = 25, probability: float = 0.8) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def potential_partner_filter(
        world: World, gameobject: GameObject, **kwargs
    ) -> bool:
        event: LifeEvent = kwargs["event"]
        rel_graph = world.get_resource(RelationshipGraph)
        if rel_graph.has_connection(
            event["PersonA"], gameobject.id
        ) and rel_graph.has_connection(gameobject.id, event["PersonA"]):
            return (
                rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                >= threshold
                and rel_graph.get_connection(gameobject.id, event["PersonA"]).romance
                >= threshold
            )
        else:
            return False

    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.SignificantOther
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.SignificantOther
        )

        person_a = world.get_gameobject(event["PersonA"])
        person_b = world.get_gameobject(event["PersonB"])

        person_a.add_component(
            Dating(
                partner_id=person_b.id,
                partner_name=str(person_b.get_component(GameCharacter).name),
            )
        )
        person_b.add_component(
            Dating(
                partner_id=person_a.id,
                partner_name=str(person_a.get_component(GameCharacter).name),
            )
        )
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="StartDating",
        roles=[
            RoleType(name="PersonA", components=[GameCharacter], filter_fn=is_single),
            RoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=join_filters(potential_partner_filter, is_single),
            ),
        ],
        effects=execute,
        probability=constant_probability(probability),
    )


def dating_break_up_event(
    threshold: int = 5, probability: float = 0.8
) -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def bind_potential_ex(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)
        dating = world.get_gameobject(event["PersonA"]).get_component(Dating)
        partner = world.get_gameobject(dating.partner_id)

        if (
            rel_graph.get_connection(event["PersonA"], dating.partner_id).romance
            < threshold
        ):
            return partner

        if (
            rel_graph.get_connection(dating.partner_id, event["PersonA"]).romance
            < threshold
        ):
            return partner

        # Just break up for no reason at all
        if world.get_resource(NeighborlyEngine).rng.random() < 0.15:
            return partner

        return None

    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).remove_tags(
            RelationshipTag.SignificantOther
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).remove_tags(
            RelationshipTag.SignificantOther
        )
        world.get_resource(LifeEventLog).record_event(event)

        world.get_gameobject(event["PersonA"]).remove_component(Dating)
        world.get_gameobject(event["PersonB"]).remove_component(Dating)

    return LifeEventType(
        name="DatingBreakUp",
        roles=[
            RoleType(name="PersonA", components=[GameCharacter, Dating]),
            RoleType(name="PersonB", binder_fn=bind_potential_ex),
        ],
        effects=execute,
        probability=constant_probability(probability),
    )


def divorce_event(threshold: int = -25, probability: float = 0.5) -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def current_partner_filter(world: World, gameobject: GameObject, **kwargs) -> bool:
        event: LifeEvent = kwargs["event"]
        rel_graph = world.get_resource(RelationshipGraph)

        if gameobject.has_component(Married):
            if gameobject.get_component(Married).partner_id == event["PersonA"]:
                return (
                    rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                    < threshold
                )

        return False

    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).remove_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).remove_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )

        world.get_gameobject(event["PersonA"]).remove_component(Married)
        world.get_gameobject(event["PersonB"]).remove_component(Married)
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="GotDivorced",
        roles=[
            RoleType(name="PersonA", components=[GameCharacter]),
            RoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=current_partner_filter,
            ),
        ],
        effects=execute,
        probability=constant_probability(probability),
    )


def marriage_event(threshold: int = 35, probability: float = 0.5) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def bind_potential_spouse(world: World, event: LifeEvent):
        character = world.get_gameobject(event["PersonA"])
        potential_spouse = world.get_gameobject(
            character.get_component(Dating).partner_id
        )
        rel_graph = world.get_resource(RelationshipGraph)

        character_meets_thresh = (
            rel_graph.get_connection(character.id, potential_spouse.id).romance
            >= threshold
        )

        potential_spouse_meets_thresh = (
            rel_graph.get_connection(potential_spouse.id, character.id).romance
            >= threshold
        )

        if character_meets_thresh and potential_spouse_meets_thresh:
            return potential_spouse

        return None

    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )

        person_a = world.get_gameobject(event["PersonA"])
        person_b = world.get_gameobject(event["PersonB"])

        person_a.remove_component(Dating)
        person_b.remove_component(Dating)

        person_a.add_component(
            Married(
                partner_id=person_b.id,
                partner_name=str(person_b.get_component(GameCharacter).name),
            )
        )
        person_b.add_component(
            Married(
                partner_id=person_a.id,
                partner_name=str(person_a.get_component(GameCharacter).name),
            )
        )
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="GotMarried",
        roles=[
            RoleType(name="PersonA", components=[GameCharacter, Dating]),
            RoleType(name="PersonB", binder_fn=bind_potential_spouse),
        ],
        effects=execute,
        probability=constant_probability(probability),
    )


def depart_due_to_unemployment() -> LifeEventType:
    def bind_unemployed_character(world: World, event: LifeEvent):
        eligible_characters: List[GameObject] = []
        for _, unemployed in world.get_component(Unemployed):
            if unemployed.duration_days > 30:
                eligible_characters.append(unemployed.gameobject)
        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)
        return None

    def effect(world: World, event: LifeEvent):
        world.get_gameobject(event["Person"]).archive()
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="DepartTown",
        roles=[RoleType(name="Person", binder_fn=bind_unemployed_character)],
        effects=effect,
        probability=constant_probability(1),
    )


def pregnancy_event() -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def can_get_pregnant_filter(world: World, gameobject: GameObject, **kwargs) -> bool:
        return gameobject.get_component(
            GameCharacter
        ).can_get_pregnant and not gameobject.has_component(Pregnant)

    def bind_current_partner(world: World, event: LifeEvent) -> Optional[GameObject]:
        person_a = world.get_gameobject(event["PersonA"])
        if person_a.has_component(Married):
            return world.get_gameobject(person_a.get_component(Married).partner_id)
        return None

    def execute(world: World, event: LifeEvent):
        due_date = SimDateTime.from_iso_str(
            world.get_resource(SimDateTime).to_iso_str()
        )
        due_date.increment(months=9)

        world.get_gameobject(event["PersonA"]).add_component(
            Pregnant(
                partner_name=str(
                    world.get_gameobject(event["PersonB"])
                    .get_component(GameCharacter)
                    .name
                ),
                partner_id=event["PersonB"],
                due_date=due_date,
            )
        )
        world.get_resource(LifeEventLog).record_event(event)

    def prob_fn(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)
        children = rel_graph.get_all_relationships_with_tags(event["PersonA"], RelationshipTag.Child)
        if len(children) >= 5:
            return 0.0
        else:
            return 5.0 - len(children) / 5.0

    return LifeEventType(
        name="GotPregnant",
        roles=[
            RoleType(
                name="PersonA",
                components=[GameCharacter],
                filter_fn=can_get_pregnant_filter,
            ),
            RoleType(name="PersonB", binder_fn=bind_current_partner),
        ],
        effects=execute,
        probability=prob_fn,
    )


def retire_event(probability: float = 0.4) -> LifeEventType:
    """
    Event for characters retiring from working after reaching elder status

    Parameters
    ----------
    probability: float
        Probability that a character will retire from their job
        when they are an elder

    Returns
    -------
    LifeEventType
        LifeEventType instance with all configuration defined
    """

    def bind_retiree(world: World, event: LifeEvent):
        eligible_characters: List[GameObject] = []
        for gid, _ in world.get_components(Elder, Occupation):
            gameobject = world.get_gameobject(gid)
            if not gameobject.has_component(Retired):
                eligible_characters.append(gameobject)
        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)
        return None

    def execute(world: World, event: LifeEvent):
        retiree = world.get_gameobject(event["Retiree"])
        retiree.remove_component(Occupation)
        retiree.add_component(Retired())
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="Retire",
        roles=[RoleType(name="Retiree", binder_fn=bind_retiree)],
        effects=execute,
        probability=constant_probability(probability),
    )


def find_own_place_event(probability: float = 0.1) -> LifeEventType:
    def bind_potential_mover(world: World, event: LifeEvent):
        eligible: List[GameObject] = []
        for gid, (_, _, _, resident) in world.get_components(
            GameCharacter, Occupation, Adult, Resident
        ):
            resident = cast(Resident, resident)
            residence = world.get_gameobject(resident.residence).get_component(
                Residence
            )
            if gid not in residence.owners:
                eligible.append(resident.gameobject)
        if eligible:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible)
        return None

    def find_vacant_residences(world: World) -> List[Residence]:
        """Try to find a vacant residence to move into"""
        return list(
            filter(
                lambda res: res.is_vacant(),
                map(lambda pair: pair[1], world.get_component(Residence)),
            )
        )

    def choose_random_vacant_residence(world: World) -> Optional[Residence]:
        """Randomly chooses a vacant residence to move into"""
        vacancies = find_vacant_residences(world)
        if vacancies:
            return world.get_resource(NeighborlyEngine).rng.choice(vacancies)
        return None

    def execute(world: World, event: LifeEvent):
        # Try to find somewhere to live
        rel_graph = world.get_resource(RelationshipGraph)
        character = world.get_gameobject(event["Character"])
        vacant_residence = choose_random_vacant_residence(world)
        if vacant_residence:
            # Move into house with any dependent children
            move_residence(character.get_component(GameCharacter), vacant_residence)
            world.get_resource(LifeEventLog).record_event(event)

        # Depart if no housing could be found
        else:
            depart = depart_event()

            residence = world.get_gameobject(
                character.get_component(Resident).residence
            ).get_component(Residence)

            depart.try_execute_event(world, Character=character)

            # Have all spouses depart
            # Allows for polygamy
            spouses = rel_graph.get_all_relationships_with_tags(
                character.id, RelationshipTag.Spouse
            )
            for rel in spouses:
                spouse = world.get_gameobject(rel.target)
                depart.try_execute_event(world, Character=spouse)

            # Have all children living in the same house depart
            children = rel_graph.get_all_relationships_with_tags(
                character.id, RelationshipTag.Child
            )
            for rel in children:
                child = world.get_gameobject(rel.target)
                if child.id in residence.residents and child.id not in residence.owners:
                    depart.try_execute_event(world, Character=child)

    return LifeEventType(
        name="FindOwnPlace",
        probability=constant_probability(probability),
        roles=[RoleType("Character", binder_fn=bind_potential_mover)],
        effects=execute,
    )


def depart_event() -> LifeEventType:
    def execute(world: World, event: LifeEvent):
        rel_graph = world.get_resource(RelationshipGraph)
        character = world.get_gameobject(event["Character"])
        character.remove_component(Present)
        # Archive GameObject instead of removing it
        character.archive()
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="Depart",
        roles=[RoleType("Character")],
        effects=execute,
        probability=constant_probability(1),
    )


def die_of_old_age(probability: float = 0.8) -> LifeEventType:
    def bind_character(world: World, event: LifeEvent):
        eligible_characters: List[GameObject] = []
        for _, (character, _) in world.get_components(GameCharacter, Present):
            character = cast(GameCharacter, character)
            if character.age >= character.character_def.lifespan:
                eligible_characters.append(character.gameobject)

        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)

        return None

    def execute(world: World, event: LifeEvent):
        death_event().try_execute_event(
            world, Deceased=world.get_gameobject(event["Character"])
        )

    return LifeEventType(
        name="DieOfOldAge",
        probability=constant_probability(probability),
        roles=[RoleType("Character", binder_fn=bind_character)],
        effects=execute,
    )


def death_event() -> LifeEventType:
    def execute(world: World, event: LifeEvent):
        deceased = world.get_gameobject(event["Deceased"])
        deceased.add_component(Deceased())
        deceased.remove_component(Present)
        # Archive GameObject instead of removing it
        deceased.archive()
        world.get_resource(LifeEventLog).record_event(event)

    return LifeEventType(
        name="Death",
        roles=[RoleType("Deceased")],
        effects=execute,
        probability=constant_probability(1),
    )
