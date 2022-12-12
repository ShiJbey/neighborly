from __future__ import annotations

from typing import Any, Dict, List

from neighborly.components.business import Occupation
from neighborly.components.character import Departed, GameCharacter
from neighborly.components.relationship import Relationships
from neighborly.components.residence import Resident
from neighborly.components.shared import Active, Age
from neighborly.core.ecs import GameObject, World
from neighborly.core.event import EventLog
from neighborly.core.settlement import Settlement
from neighborly.core.status import IOnExpire, IOnUpdate, StatusType
from neighborly.core.time import HOURS_PER_DAY, HOURS_PER_YEAR, SimDateTime
from neighborly.events import ChildBirthEvent, DepartEvent
from neighborly.utils.common import (
    check_share_residence,
    generate_child,
    set_location,
    set_residence,
)


class Pregnant(StatusType, IOnExpire):
    """
    Pregnant characters give birth when the timeout
    """

    __slots__ = "partner_id", "due_date"

    def __init__(self, partner_id: int, due_date: SimDateTime) -> None:
        super(StatusType, self).__init__()
        self.partner_id: int = partner_id
        self.due_date: SimDateTime = due_date

    @staticmethod
    def is_expired(world: World, status: GameObject) -> bool:
        pregnancy = status.get_component(Pregnant)
        return pregnancy.due_date <= world.get_resource(SimDateTime)

    @staticmethod
    def on_expire(world: World, status: GameObject) -> None:
        character = status.parent
        assert character is not None
        pregnancy = status.get_component(Pregnant)
        other_parent = world.get_gameobject(pregnancy.partner_id)
        current_date = world.get_resource(SimDateTime)
        settlement = world.get_resource(Settlement)

        baby = generate_child(
            world,
            character,
            other_parent,
        )

        settlement.increment_population()

        baby.get_component(Age).value = (
            current_date - pregnancy.due_date
        ).hours / HOURS_PER_YEAR

        baby.get_component(GameCharacter).last_name = character.get_component(
            GameCharacter
        ).last_name

        set_location(world, character, "home")

        set_residence(
            world,
            baby,
            world.get_gameobject(character.get_component(Resident).residence),
        )

        set_location(
            world,
            baby,
            "home",
        )

        # Birthing parent to child
        character.get_component(Relationships).get(baby.id).add_tags("Child")

        # Child to birthing parent
        baby.get_component(Relationships).get(character.id).add_tags("Parent")

        # Other parent to child
        other_parent.get_component(Relationships).get(baby.id).add_tags("Child")
        other_parent.get_component(Relationships).get(baby.id).add_tags("Family")

        # Child to other parent
        baby.get_component(Relationships).get(other_parent.id).add_tags("Parent")
        baby.get_component(Relationships).get(other_parent.id).add_tags("Family")

        # Create relationships with children of birthing parent
        for rel in character.get_component(Relationships).get_all_with_tags("Child"):
            if rel.target == baby.id:
                continue

            # Baby to sibling
            baby.get_component(Relationships).get(rel.target).add_tags("Sibling")
            baby.get_component(Relationships).get(rel.target).add_tags("Family")
            # Sibling to baby
            world.get_gameobject(rel.target).get_component(Relationships).get(
                baby.id
            ).add_tags("Sibling")
            world.get_gameobject(rel.target).get_component(Relationships).get(
                baby.id
            ).add_tags("Family")

        # Create relationships with children of other parent
        for rel in other_parent.get_component(Relationships).get_all_with_tags("Child"):
            if rel.target == baby.id:
                continue

            sibling = world.get_gameobject(rel.target)

            # Baby to sibling
            baby.get_component(Relationships).get(rel.target).add_tags("Sibling")

            # Sibling to baby
            sibling.get_component(Relationships).get(baby.id).add_tags("Sibling")

        # Pregnancy event dates are retro-fit to be the actual date that the
        # child was due.
        world.get_resource(EventLog).record_event(
            ChildBirthEvent(current_date, character, other_parent, baby)
        )


class Unemployed(StatusType, IOnExpire, IOnUpdate):
    __slots__ = "days_to_find_a_job", "grace_period"

    def __init__(self, days_to_find_a_job: int) -> None:
        super(StatusType, self).__init__()
        self.days_to_find_a_job: float = float(days_to_find_a_job)
        self.grace_period: float = float(days_to_find_a_job)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "days_to_find_a_job": self.days_to_find_a_job}

    @staticmethod
    def is_expired(world: World, status: GameObject) -> bool:
        unemployed = status.get_component(Unemployed)
        return unemployed.days_to_find_a_job <= 0

    @staticmethod
    def on_update(world: World, status: GameObject, elapsed_hours: int) -> None:
        status.get_component(Unemployed).days_to_find_a_job -= (
            elapsed_hours / HOURS_PER_DAY
        )

    @staticmethod
    def on_expire(world: World, status: GameObject) -> None:
        character = status.parent
        assert character
        spouses = character.get_component(Relationships).get_all_with_tags("Spouse")

        # Do not depart if one or more of the entity's spouses has a job
        if any(
            [
                world.get_gameobject(rel.target).has_component(Occupation)
                for rel in spouses
            ]
        ):
            return

        else:
            characters_to_depart: List[GameObject] = [character]

            # Have all spouses depart
            # Allows for polygamy
            for rel in spouses:
                spouse = world.get_gameobject(rel.target)
                if spouse.has_component(Active):
                    characters_to_depart.append(spouse)

            # Have all children living in the same house depart
            children = character.get_component(Relationships).get_all_with_tags("Child")
            for rel in children:
                child = world.get_gameobject(rel.target)
                if child.has_component(Active) and check_share_residence(
                    character, child
                ):
                    characters_to_depart.append(child)

            for c in characters_to_depart:
                c.add_component(Departed())
                c.remove_component(Active, immediate=True)

            event = DepartEvent(
                world.get_resource(SimDateTime), characters_to_depart, "unemployment"
            )

            world.get_resource(EventLog).record_event(event)
