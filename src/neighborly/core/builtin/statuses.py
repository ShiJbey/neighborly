from neighborly.core.ecs import World
from neighborly.core.status import Status


class ChildStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "child",
            "Character is seen as a child in the eyes of society",
        )


class AdolescentStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Adolescent",
            "Character is seen as an adolescent in the eyes of society",
        )


class YoungAdultStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Young Adult",
            "Character is seen as a young adult in the eyes of society",
        )


class AdultStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Adult",
            "Character is seen as an adult in the eyes of society",
        )


class ElderStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Senior",
            "Character is seen as a senior in the eyes of society",
        )


class RetiredStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Retired",
            "This character retired from their last occupation",
        )


class ResidentStatus(Status):
    __slots__ = "duration", "town"

    def __init__(self, town: str) -> None:
        super().__init__(
            "Resident",
            "This character is a resident of a town",
        )
        self.duration: float = 0
        self.town: str = town

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, resident_status in world.get_component(ResidentStatus):
            resident_status.duration += delta_time


class UnemployedStatus(Status):
    __slots__ = "duration"

    def __init__(self) -> None:
        super().__init__(
            "Unemployed",
            "Character doesn't have a job",
        )
        self.duration: float = 0

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, unemployed_status in world.get_component(UnemployedStatus):
            unemployed_status.duration += delta_time


class DatingStatus(Status):
    __slots__ = "duration", "partner_id", "partner_name"

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__(
            "Dating",
            "This character is in a relationship with another",
        )
        self.duration: float = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, dating_status in world.get_component(DatingStatus):
            dating_status.duration += delta_time


class MarriedStatus(Status):
    __slots__ = "duration", "partner_id", "partner_name"

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__(
            "Married",
            "This character is married to another",
        )
        self.duration = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, married_status in world.get_component(MarriedStatus):
            married_status.duration += delta_time
