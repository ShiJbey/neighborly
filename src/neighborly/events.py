from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from neighborly.ecs import GameObject, World
from neighborly.life_event import EventHistory, EventLog, LifeEvent
from neighborly.settlement import Settlement
from neighborly.time import SimDateTime


class DepartEvent(LifeEvent):
    __slots__ = "characters", "reason"

    characters: Tuple[GameObject, ...]
    reason: Optional[LifeEvent]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        characters: List[GameObject],
        reason: Optional[LifeEvent] = None,
    ) -> None:
        super().__init__(world, date)
        self.characters = tuple(characters)
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "characters": [c.uid for c in self.characters],
            "reason": self.reason.event_id if self.reason else -1,
        }

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def __str__(self) -> str:
        if self.reason:
            return "{} [@ {}] '{}' departed from '{}' because of '{}'".format(
                type(self).__name__,
                str(self.timestamp),
                " and ".join([c.name for c in self.characters]),
                self.world.resource_manager.get_resource(Settlement).name,
                type(self.reason).__name__,
            )
        else:
            return "{} [@ {}] '{}' departed from '{}'".format(
                type(self).__name__,
                str(self.timestamp),
                " and ".join([c.name for c in self.characters]),
                self.world.resource_manager.get_resource(Settlement).name,
            )


class ChangeResidenceEvent(LifeEvent):
    __slots__ = "old_residence", "new_residence", "character"

    old_residence: Optional[GameObject]
    new_residence: Optional[GameObject]
    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        old_residence: GameObject,
        new_residence: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        if old_residence is None and new_residence is None:
            raise TypeError("old_residence and new_residence cannot both be None.")
        self.character = character
        self.old_residence = old_residence
        self.new_residence = new_residence

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "old_residence": self.old_residence.uid if self.old_residence else -1,
            "new_residence": self.new_residence.uid if self.new_residence else -1,
            "character": self.character.uid,
        }

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.character.get_component(EventHistory).append(self)

    def __str__(self) -> str:
        if self.new_residence:
            return "{} [@ {}] '{}' moved into a new residence ({}).".format(
                type(self).__name__,
                str(self.timestamp),
                self.character.name,
                self.new_residence.name,
            )
        else:
            return "{} [@ {}] '{}' moved out of residence ({}).".format(
                type(self).__name__,
                str(self.timestamp),
                self.character.name,
                self.old_residence.name,
            )


class BirthEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(self, world: World, date: SimDateTime, character: GameObject) -> None:
        super().__init__(world, date)
        self.character = character

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}


class HaveChildEvent(LifeEvent):
    __slots__ = "birthing_parent", "other_parent", "baby"

    birthing_parent: GameObject
    other_parent: GameObject
    baby: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        birthing_parent: GameObject,
        other_parent: GameObject,
        baby: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.birthing_parent = birthing_parent
        self.other_parent = other_parent
        self.baby = baby

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.birthing_parent.get_component(EventHistory).append(self)
        self.other_parent.get_component(EventHistory).append(self)
        self.baby.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "birthing_parent": self.birthing_parent,
            "other_parent": self.other_parent,
            "baby": self.baby,
        }


class MarriageEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} got married.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class DivorceEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} got divorced.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class StartDatingEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} started dating.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class BreakUpEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} broke up.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class BecameAcquaintancesEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a acquaintances.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class BecomeAdolescentEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a adolescent.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class BecomeYoungAdultEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a young adult.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class BecomeAdultEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became an adult.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class BecomeSeniorEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a senior.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class DeathEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} died.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class GetPregnantEvent(LifeEvent):
    __slots__ = "pregnant_one", "partner"

    pregnant_one: GameObject
    """The character that got pregnant."""

    partner: GameObject
    """The character that impregnated the other."""

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        pregnant_one: GameObject,
        partner: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.pregnant_one = pregnant_one
        self.partner = partner

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.pregnant_one.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "pregnant_one": self.pregnant_one.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} got pregnant by {}.".format(
            type(self).__name__,
            str(self.timestamp),
            self.pregnant_one.name,
            self.partner.name,
        )
