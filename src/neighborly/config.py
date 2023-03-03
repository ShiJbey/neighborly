from __future__ import annotations

import os
import random
from typing import Any, Dict, List, Union

import pydantic

from neighborly.core.ecs import EntityPrefab
from neighborly.core.time import SimDateTime


class PluginConfig(pydantic.BaseModel):
    """
    Settings for loading and constructing a plugin

    Fields
    ----------
    name: str
        Name of the plugin's python module
    path: Optional[str]
        The path where the plugin is located
    options: Dict[str, Any]
        Parameters to pass to the plugin when constructing
        and loading it
    """

    name: str
    path: str = pydantic.Field(default_factory=lambda: os.getcwd())


class NeighborlyConfig(pydantic.BaseModel):
    seed: Union[str, int] = pydantic.Field(
        default_factory=lambda: random.randint(0, 9999999)
    )
    relationship_schema: EntityPrefab = pydantic.Field(
        default_factory=lambda: EntityPrefab()
    )
    plugins: List[Union[str, PluginConfig]] = pydantic.Field(default_factory=list)
    # Months to increment time by each simulation step
    time_increment: int = 1
    years_to_simulate: int = 50
    start_date: SimDateTime = pydantic.Field(
        default_factory=lambda: SimDateTime(1, 1, 1)
    )
    verbose: bool = True
    settings: Dict[str, Any] = pydantic.Field(default_factory=dict)

    @pydantic.validator("start_date", pre=True)  # type: ignore
    def validate_date(cls, value: Any) -> SimDateTime:
        if isinstance(value, SimDateTime):
            return value
        elif isinstance(value, str):
            return SimDateTime.from_str(value)
        raise TypeError(f"Expected str or SimDateTime, but was {type(value)}")

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**{**defaults.dict(), **data})

    class Config:
        arbitrary_types_allowed = True
