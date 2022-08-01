from neighborly.core.business import Business
from neighborly.core.ecs import Component, IEventListener, World, Event
from neighborly.core.status import Status
from neighborly.core.time import SimDateTime


class Child(Status):
    def __init__(self) -> None:
        super().__init__(
            "child",
            "Character is seen as a child in the eyes of society",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Teen(Status):
    def __init__(self) -> None:
        super().__init__(
            "Adolescent",
            "Character is seen as an adolescent in the eyes of society",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class YoungAdult(Status):
    def __init__(self) -> None:
        super().__init__(
            "Young Adult",
            "Character is seen as a young adult in the eyes of society",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Adult(Status):
    def __init__(self) -> None:
        super().__init__(
            "Adult",
            "Character is seen as an adult in the eyes of society",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Elder(Status):
    def __init__(self) -> None:
        super().__init__(
            "Senior",
            "Character is seen as a senior in the eyes of society",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Deceased(Status):
    def __init__(self) -> None:
        super().__init__(
            "Deceased",
            "This character is dead",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Retired(Status):
    def __init__(self) -> None:
        super().__init__(
            "Retired",
            "This character retired from their last occupation",
        )

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Resident(Status):
    __slots__ = "duration", "town"

    def __init__(self, town: str) -> None:
        super().__init__(
            "Resident",
            "This character is a resident of a town",
        )
        self.duration: float = 0
        self.town: str = town

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls(**kwargs)

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, resident_status in world.get_component(Resident):
            resident_status.duration += delta_time


class Dependent(Status):
    def __init__(self) -> None:
        super().__init__("Dependent", "This character is dependent on their parents")

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()


class Unemployed(Status):
    __slots__ = "duration"

    def __init__(self) -> None:
        super().__init__(
            "Unemployed",
            "Character doesn't have a job",
        )
        self.duration: float = 0

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls()

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, unemployed_status in world.get_component(Unemployed):
            unemployed_status.duration += delta_time


class Dating(Status):
    __slots__ = "duration", "partner_id", "partner_name"

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__(
            "Dating",
            "This character is in a relationship with another",
        )
        self.duration: float = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls(**kwargs)

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, dating_status in world.get_component(Dating):
            dating_status.duration += delta_time


class Married(Status):
    __slots__ = "duration", "partner_id", "partner_name"

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__(
            "Married",
            "This character is married to another",
        )
        self.duration = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls(**kwargs)

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        for _, married_status in world.get_component(Married):
            married_status.duration += delta_time


class InRelationship(Status):
    __slots__ = "duration", "partner_id", "partner_name", "relationship_type"

    def __init__(
        self, relationship_type: str, partner_id: int, partner_name: str
    ) -> None:
        super().__init__(
            "Married",
            "This character is married to another",
        )
        self.relationship_type: str = relationship_type
        self.duration = 0.0
        self.partner_id: int = partner_id
        self.partner_name: str = partner_name

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls(**kwargs)

    @staticmethod
    def system_fn(world: World, **kwargs) -> None:
        delta_time: float = world.get_resource(SimDateTime).delta_time
        for _, married_status in world.get_component(Married):
            married_status.duration += delta_time


class BusinessOwner(Status, IEventListener):
    __slots__ = "duration", "business_id", "business_name"

    def __init__(self, business_id: int, business_name: str) -> None:
        super().__init__(
            "Business Owner",
            "This character owns a business",
        )
        self.duration = 0.0
        self.business_id: int = business_id
        self.business_name: str = business_name

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls(**kwargs)

    def will_handle_event(self, event: Event) -> bool:
        return True

    def handle_event(self, event: Event) -> bool:
        event_type = event.get_type()
        if event_type == "death":
            print("Character died and are no longer a business owner.")
            # Remove the character from their work position
            world = self.gameobject.world
            workplace = world.get_gameobject(self.business_id).get_component(Business)
            workplace.set_owner(None)
            self.gameobject.remove_component(BusinessOwner)
        return True


class Pregnant(Status):
    def __init__(
        self, partner_name: str, partner_id: int, due_date: SimDateTime
    ) -> None:
        super().__init__("Pregnant", "This character is pregnant")
        self.partner_name: str = partner_name
        self.partner_id: int = partner_id
        self.due_date: SimDateTime = due_date

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return cls(**kwargs)
