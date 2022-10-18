import enum
from typing import Dict, Optional

from neighborly.core.character import LifeStageAges
from neighborly.core.ecs import Component, World, component_info, remove_on_archive
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.time import SimDateTime


class Human(Component):
    """Marks an entity as a Human"""

    pass


class MaxCapacity(Component):

    __slots__ = "capacity"

    def __init__(self, capacity: int) -> None:
        super().__init__()
        self.capacity = capacity


class Name(Component):
    """
    The string name of an entity
    """

    __slots__ = "name"

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.name = name


class Age(Component):
    """
    Tracks the number of years old that an entity is
    """

    __slots__ = "age"

    def __init__(self, age: float = 0.0) -> None:
        super().__init__()
        self.age: float = age


class CanAge(Component):
    """
    This component flags an entity as being able to age when time passes.
    """

    pass


class Mortal(Component):
    pass


class Immortal(Component):
    pass


class OpenToPublic(Component):
    """
    This is an empty component that flags a location as one that characters
    may travel to when they don't have somewhere to be in the Routine component
    """

    pass


class GenderValue(enum.Enum):
    Male = "male"
    Female = "female"
    NonBinary = "non-binary"


class Gender(Component):

    __slots__ = "gender"

    def __init__(self, gender: GenderValue) -> None:
        super().__init__()
        self.gender: GenderValue = gender

    @classmethod
    def create(cls, world: World, **kwargs) -> Component:
        rng = world.get_resource(NeighborlyEngine).rng
        choice = rng.choice(list(GenderValue))
        return cls(gender=choice)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(gender={self.gender})"


class CurrentLocation(Component):
    """Tracks the current location of this game object"""

    __slots__ = "location"

    def __init__(self) -> None:
        super().__init__()
        self.location: Optional[int] = None


class Lifespan(Component):
    """How long this entity usually lives"""

    __slots__ = "lifespan"

    def __init__(self, lifespan: float) -> None:
        super().__init__()
        self.lifespan: float = lifespan


class LocationAliases(Component):
    """
    Keeps record of strings mapped the IDs of locations in the world
    """

    __slots__ = "aliases"

    def __init__(self) -> None:
        super().__init__()
        self.aliases: Dict[str, int] = {}


class LifeStages(Component):
    """Tracks what stage of life an entity is in"""

    __slots__ = "stages"

    def __init__(self, stages: LifeStageAges) -> None:
        super().__init__()
        self.stages: LifeStageAges = stages


class CanGetPregnant(Component):
    """Indicates that an entity is capable of giving birth"""

    pass


@component_info(
    name="child", description="Character is seen as a child in the eyes of society"
)
class Child(Component):
    pass


@component_info(
    "Adolescent",
    "Character is seen as an adolescent in the eyes of society",
)
class Teen(Component):
    pass


@component_info(
    "Young Adult",
    "Character is seen as a young adult in the eyes of society",
)
class YoungAdult(Component):
    pass


@component_info(
    "Adult",
    "Character is seen as an adult in the eyes of society",
)
class Adult(Component):
    pass


@component_info(
    "Senior",
    "Character is seen as a senior in the eyes of society",
)
class Elder(Component):
    pass


@component_info(
    "Deceased",
    "This entity is dead",
)
class Deceased(Component):
    pass


@component_info("Retired", "This entity retired from their last occupation")
class Retired(Component):
    pass


@component_info("Dependent", "This entity is dependent on their parents")
class Dependent(Component):
    pass


@component_info(
    "Dating",
    "This entity is in a relationship with another",
)
@remove_on_archive
class Dating(Component):
    __slots__ = "duration_years", "partner_id", "partner_name"

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__()
        self.duration_years: float = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    def on_archive(self) -> None:
        """Remove status on this entity and the partner"""
        self.gameobject.world.get_gameobject(self.partner_id).remove_component(
            type(self)
        )


@component_info(
    "Married",
    "This entity is married to another",
)
@remove_on_archive
class Married(Component):
    __slots__ = "duration_years", "partner_id", "partner_name"

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__()
        self.duration_years: float = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    def on_archive(self) -> None:
        """Remove status on this entity and the partner"""
        if self.gameobject.world.get_gameobject(self.partner_id).has_component(
            type(self)
        ):
            self.gameobject.world.get_gameobject(self.partner_id).remove_component(
                type(self)
            )


@remove_on_archive
class Pregnant(Component):

    __slots__ = "partner_name", "partner_id", "due_date"

    def __init__(
        self, partner_name: str, partner_id: int, due_date: SimDateTime
    ) -> None:
        super().__init__()
        self.partner_name: str = partner_name
        self.partner_id: int = partner_id
        self.due_date: SimDateTime = due_date


@component_info("Male", "This entity is perceived as masculine.")
class Male(Component):
    pass


@component_info("Female", "This entity is perceived as feminine.")
class Female(Component):
    pass


@component_info("NonBinary", "This entity is perceived as non-binary.")
class NonBinary(Component):
    pass


@component_info("College Graduate", "This entity graduated from college.")
class CollegeGraduate(Component):
    pass


@component_info("Active", "This entity is in the town and active in the simulation")
@remove_on_archive
class Active(Component):
    pass
