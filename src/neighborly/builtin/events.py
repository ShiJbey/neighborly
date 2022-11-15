from __future__ import annotations

from typing import Any, List, Optional, Tuple, cast

import neighborly.core.query as querylib
from neighborly.builtin.components import (
    Active,
    Adult,
    Age,
    CanGetPregnant,
    Deceased,
    Departed,
    Elder,
    Lifespan,
    OpenToPublic,
    Pregnant,
    Retired,
    Vacant,
)
from neighborly.builtin.helpers import move_residence, move_to_location
from neighborly.builtin.role_filters import (
    friendship_gt,
    friendship_lt,
    is_single,
    relationship_has_tags,
    romance_gt,
    romance_lt,
)
from neighborly.core.business import (
    Business,
    ClosedForBusiness,
    Occupation,
    OpenForBusiness,
    Unemployed,
)
from neighborly.core.character import CharacterName, GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.event import Event
from neighborly.core.life_event import (
    ILifeEvent,
    LifeEvent,
    LifeEventRoleType,
    PatternLifeEvent,
)
from neighborly.core.relationship import Relationships
from neighborly.core.residence import Residence, Resident
from neighborly.core.time import SimDateTime


def become_friends_event(
    threshold: float = 0.7, probability: float = 1.0
) -> ILifeEvent:
    """Defines an event where two characters become friends"""

    def effect(world: World, event: Event):
        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).add_tags("Friend")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).add_tags("Friend")

    return PatternLifeEvent(
        name="BecomeFriends",
        pattern=querylib.Query(
            find=("Initiator", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "Initiator"),
                querylib.where(querylib.has_components(Active), "Initiator"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("Initiator", "Other")),
                querylib.where(friendship_gt(threshold), "Initiator", "Other"),
                querylib.where(friendship_gt(threshold), "Other", "Initiator"),
                querylib.where_not(
                    relationship_has_tags("Friend"), "Initiator", "Other"
                ),
            ],
        ),
        effect=effect,
        probability=probability,
    )


def become_enemies_event(
    threshold: float = 0.3, probability: float = 1.0
) -> ILifeEvent:
    """Defines an event where two characters become friends"""

    def effect(world: World, event: Event):
        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).add_tags("Enemy")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).add_tags("Enemy")

    return PatternLifeEvent(
        name="BecomeEnemies",
        pattern=querylib.Query(
            find=("Initiator", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "Initiator"),
                querylib.where(querylib.has_components(Active), "Initiator"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("Initiator", "Other")),
                querylib.where(friendship_lt(threshold), "Initiator", "Other"),
                querylib.where(friendship_lt(threshold), "Other", "Initiator"),
                querylib.where_not(
                    relationship_has_tags("Enemy"), "Initiator", "Other"
                ),
            ],
        ),
        effect=effect,
        probability=probability,
    )


def start_dating_event(threshold: float = 0.7, probability: float = 1.0) -> ILifeEvent:
    """Defines an event where two characters become friends"""

    def effect(world: World, event: Event):
        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).add_tags("Dating", "Significant Other")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).add_tags("Dating", "Significant Other")

    return PatternLifeEvent(
        name="StartDating",
        pattern=querylib.Query(
            find=("Initiator", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "Initiator"),
                querylib.where(querylib.has_components(Active), "Initiator"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("Initiator", "Other")),
                querylib.where(romance_gt(threshold), "Initiator", "Other"),
                querylib.where(romance_gt(threshold), "Other", "Initiator"),
                querylib.where_not(
                    relationship_has_tags("Significant Other"), "Other", "Other_Curr_SO"
                ),
                querylib.where_not(
                    relationship_has_tags("Significant Other"),
                    "Initiator",
                    "Initiator_Curr_SO",
                ),
                querylib.where_not(
                    relationship_has_tags("Significant Other"), "Other", "Initiator"
                ),
                querylib.where_not(
                    relationship_has_tags("Family"), "Other", "Initiator"
                ),
                querylib.where(
                    querylib.to_clause(is_single, GameCharacter), "Initiator"
                ),
                querylib.where(querylib.to_clause(is_single, GameCharacter), "Other"),
            ],
        ),
        effect=effect,
        probability=probability,
    )


def stop_dating_event(threshold: float = 0.4, probability: float = 1.0) -> ILifeEvent:
    """Defines an event where two characters become friends"""

    def effect(world: World, event: Event):
        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).remove_tags("Dating", "Significant Other")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).remove_tags("Dating", "Significant Other")

    return PatternLifeEvent(
        name="DatingBreakUp",
        pattern=querylib.Query(
            find=("Initiator", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "Initiator"),
                querylib.where(querylib.has_components(Active), "Initiator"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("Initiator", "Other")),
                querylib.where(romance_lt(threshold), "Initiator", "Other"),
                querylib.where(romance_lt(threshold), "Other", "Initiator "),
                querylib.where(relationship_has_tags("Dating"), "Initiator", "Other"),
            ],
        ),
        effect=effect,
        probability=probability,
    )


def divorce_event(threshold: float = 0.4, probability: float = 1.0) -> ILifeEvent:
    """Defines an event where two characters become friends"""

    def effect(world: World, event: Event):
        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).remove_tags("Spouse", "Significant Other")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).remove_tags("Spouse", "Significant Other")

    return PatternLifeEvent(
        name="Divorce",
        pattern=querylib.Query(
            find=("Initiator", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "Initiator"),
                querylib.where(querylib.has_components(Active), "Initiator"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("Initiator", "Other")),
                querylib.where(romance_lt(threshold), "Initiator", "Other"),
                querylib.where(romance_lt(threshold), "Other", "Initiator "),
                querylib.where(relationship_has_tags("Spouse"), "Initiator", "Other"),
            ],
        ),
        effect=effect,
        probability=probability,
    )


def marriage_event(threshold: float = 0.7, probability: float = 1.0) -> ILifeEvent:
    """Defines an event where two characters become friends"""

    def effect(world: World, event: Event):
        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).add_tags("Spouse", "Significant Other")

        world.get_gameobject(event["Initiator"]).get_component(Relationships).get(
            event["Other"]
        ).remove_tags("Dating")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).add_tags("Spouse", "Significant Other")

        world.get_gameobject(event["Other"]).get_component(Relationships).get(
            event["Initiator"]
        ).remove_tags("Dating")

    return PatternLifeEvent(
        name="GetMarried",
        pattern=querylib.Query(
            find=("Initiator", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "Initiator"),
                querylib.where(querylib.has_components(Active), "Initiator"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("Initiator", "Other")),
                querylib.where(romance_gt(threshold), "Initiator", "Other"),
                querylib.where(romance_gt(threshold), "Other", "Initiator "),
                querylib.where(relationship_has_tags("Dating"), "Initiator", "Other"),
            ],
        ),
        effect=effect,
        probability=probability,
    )


def depart_due_to_unemployment() -> ILifeEvent:
    def bind_unemployed_character(
        world: World, event: Event, candidate: Optional[GameObject]
    ):
        eligible_characters: List[GameObject] = []
        for _, (unemployed, _) in world.get_components(Unemployed, Active):
            if unemployed.duration_days > 30:
                eligible_characters.append(unemployed.gameobject)
        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)
        return None

    def effect(world: World, event: Event):
        departed = world.get_gameobject(event["Person"])
        departed.remove_component(Active)
        departed.add_component(Departed())
        move_to_location(world, departed, None)

    return LifeEvent(
        name="DepartDueToUnemployment",
        roles=[LifeEventRoleType(name="Person", binder_fn=bind_unemployed_character)],
        effect=effect,
        probability=1,
    )


def pregnancy_event() -> ILifeEvent:
    """Defines an event where two characters stop dating"""

    def execute(world: World, event: Event):
        due_date = SimDateTime.from_iso_str(
            world.get_resource(SimDateTime).to_iso_str()
        )
        due_date.increment(months=9)

        world.get_gameobject(event["PregnantOne"]).add_component(
            Pregnant(
                partner_name=str(
                    world.get_gameobject(event["Other"]).get_component(CharacterName)
                ),
                partner_id=event["Other"],
                due_date=due_date,
            )
        )

    def prob_fn(world: World, event: Event):
        gameobject = world.get_gameobject(event["PregnantOne"])
        children = gameobject.get_component(Relationships).get_all_with_tags("Child")
        if len(children) >= 5:
            return 0.0
        else:
            return 4.0 - len(children) / 8.0

    return PatternLifeEvent(
        name="GotPregnant",
        pattern=querylib.Query(
            find=("PregnantOne", "Other"),
            clauses=[
                querylib.where(querylib.has_components(GameCharacter), "PregnantOne"),
                querylib.where(querylib.has_components(Active), "PregnantOne"),
                querylib.where(querylib.has_components(CanGetPregnant), "PregnantOne"),
                querylib.where_not(querylib.has_components(Pregnant), "PregnantOne"),
                querylib.where(querylib.has_components(GameCharacter), "Other"),
                querylib.where(querylib.has_components(Active), "Other"),
                querylib.ne_(("PregnantOne", "Other")),
                querylib.where_any(
                    querylib.where(
                        relationship_has_tags("Dating"), "PregnantOne", "Other"
                    ),
                    querylib.where(
                        relationship_has_tags("Married"), "PregnantOne", "Other"
                    ),
                ),
            ],
        ),
        effect=execute,
        probability=prob_fn,
    )


def retire_event(probability: float = 0.4) -> ILifeEvent:
    """
    Event for characters retiring from working after reaching elder status

    Parameters
    ----------
    probability: float
        Probability that an entity will retire from their job
        when they are an elder

    Returns
    -------
    LifeEvent
        LifeEventType instance with all configuration defined
    """

    def bind_retiree(world: World, event: Event, candidate: Optional[GameObject]):
        eligible_characters: List[GameObject] = []
        for gid, _ in world.get_components(Elder, Occupation, Active):
            gameobject = world.get_gameobject(gid)
            if not gameobject.has_component(Retired):
                eligible_characters.append(gameobject)
        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)
        return None

    def bind_business(world: World, event: Event, candidate: Optional[GameObject]):
        return world.get_gameobject(
            world.get_gameobject(event["Retiree"]).get_component(Occupation).business
        )

    def execute(world: World, event: Event):
        retiree = world.get_gameobject(event["Retiree"])
        retiree.add_component(Retired())

    return LifeEvent(
        name="Retire",
        roles=[
            LifeEventRoleType(name="Retiree", binder_fn=bind_retiree),
            LifeEventRoleType(name="Business", binder_fn=bind_business),
        ],
        effect=execute,
        probability=probability,
    )


def find_own_place_event(probability: float = 0.1) -> ILifeEvent:
    def bind_potential_mover(world: World) -> List[Tuple[Any, ...]]:
        eligible: List[Tuple[Any, ...]] = []

        for gid, (_, _, _, resident, _) in world.get_components(
            GameCharacter, Occupation, Adult, Resident, Active
        ):
            resident = cast(Resident, resident)
            residence = world.get_gameobject(resident.residence).get_component(
                Residence
            )
            if gid not in residence.owners:
                eligible.append((gid,))

        return eligible

    def find_vacant_residences(world: World) -> List[Residence]:
        """Try to find a vacant residence to move into"""
        return list(
            map(lambda pair: pair[1][0], world.get_components(Residence, Vacant))
        )

    def choose_random_vacant_residence(world: World) -> Optional[Residence]:
        """Randomly chooses a vacant residence to move into"""
        vacancies = find_vacant_residences(world)
        if vacancies:
            return world.get_resource(NeighborlyEngine).rng.choice(vacancies)
        return None

    def execute(world: World, event: Event):
        # Try to find somewhere to live
        character = world.get_gameobject(event["Character"])
        vacant_residence = choose_random_vacant_residence(world)
        if vacant_residence:
            # Move into house with any dependent children
            move_residence(character, vacant_residence.gameobject)

        # Depart if no housing could be found
        else:
            depart = depart_event()

            residence = world.get_gameobject(
                character.get_component(Resident).residence
            ).get_component(Residence)

            depart.try_execute_event(world, Character=character)

            # Have all spouses depart
            # Allows for polygamy
            for rel in character.get_component(Relationships).get_all_with_tags(
                "Spouse"
            ):
                spouse = world.get_gameobject(rel.target)
                depart.try_execute_event(world, Character=spouse)

            # Have all children living in the same house depart
            for rel in character.get_component(Relationships).get_all_with_tags(
                "Child"
            ):
                child = world.get_gameobject(rel.target)
                if child.id in residence.residents and child.id not in residence.owners:
                    depart.try_execute_event(world, Character=child)

    return PatternLifeEvent(
        name="FindOwnPlace",
        probability=probability,
        pattern=querylib.Query(
            ("Character",), [querylib.where(bind_potential_mover, "Character")]
        ),
        effect=execute,
    )


def depart_event() -> ILifeEvent:
    def execute(world: World, event: Event):
        character = world.get_gameobject(event["Character"])
        character.remove_component(Active)
        character.add_component(Departed())
        move_to_location(world, character, None)

    return LifeEvent(
        name="Depart",
        roles=[LifeEventRoleType("Character")],
        effect=execute,
        probability=1,
    )


def die_of_old_age(probability: float = 0.8) -> ILifeEvent:
    def execute(world: World, event: Event) -> None:
        deceased = world.get_gameobject(event["Deceased"])
        deceased.add_component(Deceased())
        deceased.remove_component(Active)

    return PatternLifeEvent(
        name="DieOfOldAge",
        probability=probability,
        pattern=querylib.Query(
            ("Deceased",),
            [
                querylib.where(
                    querylib.has_components(GameCharacter, Active), "Deceased"
                ),
                querylib.where(
                    querylib.component_attr(Age, "value"), "Deceased", "Age"
                ),
                querylib.where(
                    querylib.component_attr(Lifespan, "value"), "Deceased", "Lifespan"
                ),
                querylib.ge_(("Age", "Lifespan")),
            ],
        ),
        effect=execute,
    )


def death_event() -> ILifeEvent:
    def execute(world: World, event: Event):
        deceased = world.get_gameobject(event["Deceased"])
        deceased.add_component(Deceased())
        deceased.remove_component(Active)
        move_to_location(world, deceased, None)

    return LifeEvent(
        name="Death",
        roles=[LifeEventRoleType("Deceased")],
        effect=execute,
        probability=1.0,
    )


def go_out_of_business_event() -> ILifeEvent:
    def effect(world: World, event: Event):
        business = world.get_gameobject(event["Business"])
        business.remove_component(OpenForBusiness)
        business.add_component(ClosedForBusiness())
        if business.has_component(OpenToPublic):
            business.remove_component(OpenToPublic)

    def probability_fn(world: World, event: Event) -> float:
        business = world.get_gameobject(event["Business"])
        lifespan = business.get_component(Lifespan).value
        age = business.get_component(Age).value
        if age < lifespan:
            return age / lifespan
        else:
            return 0.8

    return PatternLifeEvent(
        name="GoOutOfBusiness",
        pattern=querylib.Query(
            find=("Business",),
            clauses=[
                querylib.where(querylib.has_components(Business), "Business"),
                querylib.where(querylib.has_components(OpenForBusiness), "Business"),
                querylib.where(querylib.has_components(Active), "Business"),
            ],
        ),
        effect=effect,
        probability=probability_fn,
    )
