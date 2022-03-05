from dataclasses import dataclass
from typing import List, Optional

from neighborly.core import name_generation as name_gen
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


@dataclass(frozen=True)
class BusinessConfig:
    name: str
    business_type: str


class Business(Component):
    __slots__ = "config", "name", "owner", "employees"

    def __init__(
            self,
            config: BusinessConfig,
            name: str,
            owner: Optional[int] = None,
            employees: Optional[List[int]] = None,
    ) -> None:
        super().__init__()
        self.config: BusinessConfig = config
        self.name: str = name
        self.owner: Optional[int] = owner
        self.employees: List[int] = [*employees] if employees else []


class BusinessFactory(AbstractFactory):
    """Create instances of the default business component"""

    def __init__(self) -> None:
        super().__init__("Business")

    def create(self, spec: ComponentSpec) -> Business:
        name = name_gen.get_name(spec["name"])

        conf = BusinessConfig(
            business_type=spec["business type"],
            name=spec["name"]
        )

        return Business(conf, name)
