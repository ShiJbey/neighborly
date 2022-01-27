from dataclasses import dataclass
from typing import List, Optional, TypeVar, Type

from neighborly.core.authoring import AbstractConstructor, CreationData, Component
from neighborly.core.name_generation import get_name

_T = TypeVar("_T", bound=Component)


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

    def load_data(self, creation_data: CreationData) -> bool:
        """Load data to from creation data"""
        return True


class DefaultBusinessConstructor(AbstractConstructor[Business]):
    """Create instances of the default business component"""

    def create(self, creation_data: CreationData) -> Optional[Business]:
        try:
            conf = BusinessConfig(**creation_data.get_node().get_attributes())

            name = get_name(conf.name)

            return Business(conf, name)
        except:
            return None
