from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class BusinessConfig:
    name: str
    business_type: str


class Business:

    __slots__ = "config", "name", "owner", "employees"

    def __init__(
        self,
        config: BusinessConfig,
        name: str,
        owner: Optional[int] = None,
        employees: Optional[List[int]] = None,
    ) -> None:
        self.config: BusinessConfig = config
        self.name: str = name
        self.owner: Optional[int] = owner
        self.employees: List[int] = [*employees] if employees else []
