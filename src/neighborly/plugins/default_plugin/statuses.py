from typing import Dict, Any

from neighborly.core.ecs import GameObject
from neighborly.core.status import StatusType, Status


class AdultStatusType(StatusType):

    def __init__(self) -> None:
        super().__init__(
            "Adult",
            "Character is seen as an adult in the eyes of society",
        )


class SeniorStatusType(StatusType):

    def __init__(self) -> None:
        super().__init__(
            "Senior",
            "Character is seen as a senior in the eyes of society",
        )


class DatingStatusType(StatusType):

    def __init__(self) -> None:
        def fn(game_object: GameObject, metadata: Dict[str, Any], **kwargs) -> bool:
            metadata['duration'] += kwargs['delta_time']
            return True

        super().__init__(
            "Dating",
            "This character is in a relationship with another",
            fn
        )


class MarriedStatusType(StatusType):

    def __init__(self) -> None:
        def fn(game_object: GameObject, metadata: Dict[str, Any], **kwargs) -> bool:
            metadata['duration'] += kwargs['delta_time']
            return True

        super().__init__(
            "Married",
            "This character is married to another",
            fn
        )


class DatingStatus(Status):

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__(StatusType.get_registered_type("Dating"), {
            "partner_name": partner_name,
            "partner_id": partner_id,
            "duration": 0
        })


class MarriedStatus(Status):

    def __init__(self, partner_id: int, partner_name: str) -> None:
        super().__init__(StatusType.get_registered_type("Married"), {
            "partner_name": partner_name,
            "partner_id": partner_id,
            "duration": 0
        })
