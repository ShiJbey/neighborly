from __future__ import annotations

from typing import List, Optional

from neighborly.builtin.role_filters import is_single, is_unemployed
from neighborly.builtin.statuses import (
    Dating,
    Elder,
    Married,
    Pregnant,
    Retired,
    Unemployed,
)
from neighborly.core.business import Business, Occupation, OccupationTypeLibrary
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    EventRoleType,
    LifeEvent,
    LifeEventType,
    join_filters,
)
from neighborly.core.relationship import RelationshipGraph, RelationshipTag
from neighborly.core.time import SimDateTime


def hire_employee_event() -> LifeEventType:
    def hiring_business_role() -> EventRoleType:
        """Defines a Role for a business with job opening"""

        def help_wanted(world: World, gameobject: GameObject, **kwargs) -> bool:
            business = gameobject.get_component(Business)
            return len(business.get_open_positions()) > 0

        return EventRoleType(
            "HiringBusiness", components=[Business], filter_fn=help_wanted
        )

    def cb(world: World, event: LifeEvent):
        engine = world.get_resource(NeighborlyEngine)
        character = world.get_gameobject(event["Unemployed"]).get_component(
            GameCharacter
        )
        business = world.get_gameobject(event["HiringBusiness"]).get_component(Business)

        position = engine.rng.choice(business.get_open_positions())

        character.gameobject.remove_component(Unemployed)

        business.add_employee(character.gameobject.id, position)
        character.gameobject.add_component(
            Occupation(
                OccupationTypeLibrary.get(position),
                business.gameobject.id,
            )
        )

    return LifeEventType(
        "HiredAtBusiness",
        roles=[
            hiring_business_role(),
            EventRoleType(
                "Unemployed", components=[GameCharacter], filter_fn=is_unemployed
            ),
        ],
        execute_fn=cb,
    )


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
            if (
                world.has_gameobject(rel.target)
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
                eligible_characters.append(world.get_gameobject(rel.target))

        if eligible_characters:
            return engine.rng.choice(eligible_characters)
        return None

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)
        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.Friend
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.Friend
        )

    return LifeEventType(
        name="BecomeFriends",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(name="PersonB", binder_fn=bind_potential_friend),
        ],
        execute_fn=execute,
        probability=probability,
    )


def become_enemies_event(
    threshold: int = -25, probability: float = 1.0
) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def potential_enemy_filter(world: World, gameobject: GameObject, **kwargs) -> bool:
        event: LifeEvent = kwargs["event"]
        rel_graph = world.get_resource(RelationshipGraph)
        if rel_graph.has_connection(
            event["PersonA"], gameobject.id
        ) and rel_graph.has_connection(gameobject.id, event["PersonA"]):
            return (
                rel_graph.get_connection(event["PersonA"], gameobject.id).friendship
                <= threshold
                and rel_graph.get_connection(gameobject.id, event["PersonA"]).friendship
                <= threshold
                and not rel_graph.get_connection(
                    event["PersonA"], gameobject.id
                ).has_tags(RelationshipTag.Enemy)
            )
        else:
            return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)
        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.Enemy
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.Enemy
        )

    return LifeEventType(
        name="BecomeEnemies",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=potential_enemy_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def start_dating_event(threshold: int = 25, probability: float = 0.5) -> LifeEventType:
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

    def execute(world: World, event: LifeEvent) -> None:
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

    return LifeEventType(
        name="StartDating",
        roles=[
            EventRoleType(
                name="PersonA", components=[GameCharacter], filter_fn=is_single
            ),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=join_filters(potential_partner_filter, is_single),
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def dating_break_up_event(
    threshold: int = -15, probability: float = 0.5
) -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def current_partner_filter(world: World, gameobject: GameObject, **kwargs) -> bool:
        event: LifeEvent = kwargs["event"]
        rel_graph = world.get_resource(RelationshipGraph)

        if gameobject.has_component(Dating):
            if gameobject.get_component(Dating).partner_id == event["PersonA"]:
                return (
                    rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                    < threshold
                )

        return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).remove_tags(
            RelationshipTag.SignificantOther
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).remove_tags(
            RelationshipTag.SignificantOther
        )

        world.get_gameobject(event["PersonA"]).remove_component(Dating)
        world.get_gameobject(event["PersonB"]).remove_component(Dating)

    return LifeEventType(
        name="DatingBreakUp",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=current_partner_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
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

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).remove_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).remove_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )

        world.get_gameobject(event["PersonA"]).remove_component(Married)
        world.get_gameobject(event["PersonB"]).remove_component(Married)

    return LifeEventType(
        name="GotDivorced",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=current_partner_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def marriage_event(threshold: int = 35, probability: float = 0.5) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def potential_partner_filter(
        world: World, gameobject: GameObject, **kwargs
    ) -> bool:
        event: LifeEvent = kwargs["event"]
        rel_graph = world.get_resource(RelationshipGraph)
        if (
            gameobject.has_component(Dating)
            and gameobject.get_component(Dating).partner_id == event["PersonA"]
        ):
            if rel_graph.has_connection(
                event["PersonA"], gameobject.id
            ) and rel_graph.has_connection(gameobject.id, event["PersonA"]):
                return (
                    rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                    >= threshold
                    and rel_graph.get_connection(
                        gameobject.id, event["PersonA"]
                    ).romance
                    >= threshold
                )

        return False

    def execute(world: World, event: LifeEvent) -> None:
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

    return LifeEventType(
        name="GotMarried",
        roles=[
            EventRoleType(
                name="PersonA", components=[GameCharacter], filter_fn=is_single
            ),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=join_filters(potential_partner_filter, is_single),
            ),
        ],
        execute_fn=execute,
        probability=probability,
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

    return LifeEventType(
        name="DepartTown",
        roles=[EventRoleType(name="Person", binder_fn=bind_unemployed_character)],
        execute_fn=effect,
    )


def pregnancy_event(probability: float = 0.3) -> LifeEventType:
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

    def execute(world: World, event: LifeEvent) -> None:
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

    return LifeEventType(
        name="GotDivorced",
        roles=[
            EventRoleType(
                name="PersonA",
                components=[GameCharacter],
                filter_fn=can_get_pregnant_filter,
            ),
            EventRoleType(name="PersonB", binder_fn=bind_current_partner),
        ],
        execute_fn=execute,
        probability=probability,
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

    return LifeEventType(
        name="Retire",
        roles=[EventRoleType(name="Retiree", binder_fn=bind_retiree)],
        execute_fn=execute,
        probability=probability,
    )
