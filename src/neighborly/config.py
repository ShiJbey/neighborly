from __future__ import annotations

import os
import random
import re
from typing import Any, Dict, List, Union

import pydantic

from neighborly.core.time import SimDateTime, TimeDelta


class PluginConfig(pydantic.BaseModel):
    """settings for loading and constructing a plugin."""

    name: str
    """Name of the plugin's python module."""

    path: str = pydantic.Field(default_factory=lambda: os.getcwd())
    """The path where the plugin is located."""

    options: Dict[str, Any] = pydantic.Field(default_factory=dict)
    """Parameters to pass to the plugin when constructing and loading it."""


class RelationshipSchema(pydantic.BaseModel):
    """Prefab information specifying components for Relationship GameObjects."""

    components: Dict[str, Dict[str, Any]] = pydantic.Field(default_factory=dict)
    """The component information for relationship instance."""


class NeighborlyConfig(pydantic.BaseModel):
    """Configuration settings for a Neighborly simulation instance."""

    seed: Union[str, int] = pydantic.Field(
        default_factory=lambda: random.randint(0, 9999999)
    )
    """A value used to seed the random number generator."""

    relationship_schema: RelationshipSchema = pydantic.Field(
        default_factory=RelationshipSchema
    )
    """The default component configuration of new Relationship GameObjects."""

    plugins: List[PluginConfig] = pydantic.Field(default_factory=list)
    """Configuration information for plugins to import before running the simulation."""

    time_increment: TimeDelta = TimeDelta(hours=4)
    """The amount of time to advance the current date by each timestep."""

    years_to_simulate: int = 50
    """The number of years to simulate."""

    start_date: SimDateTime = pydantic.Field(
        default_factory=lambda: SimDateTime(1, 1, 1)
    )
    """The starting date of the simulation before world generation."""

    verbose: bool = True
    """Toggle verbose logging."""

    settings: Dict[str, Any] = pydantic.Field(default_factory=dict)
    """Miscellaneous keyword settings."""

    @pydantic.validator("plugins", pre=True, each_item=True)  # type: ignore
    @classmethod
    def _validate_plugins(cls, value: Any) -> PluginConfig:
        if isinstance(value, PluginConfig):
            return value
        elif isinstance(value, str):
            return PluginConfig(name=value)
        elif isinstance(value, dict):
            return PluginConfig(
                name=value["name"],  # type: ignore
                path=value.get("path", "."),  # type: ignore
                options=value.get("options", {}),  # type: ignore
            )
        raise TypeError(f"Expected str or SimDateTime, but was {type(value)}")

    @pydantic.validator("start_date", pre=True)  # type: ignore
    @classmethod
    def _validate_date(cls, value: Any) -> SimDateTime:
        if isinstance(value, SimDateTime):
            return value
        elif isinstance(value, str):
            return SimDateTime.from_str(value)
        raise TypeError(f"Expected str or SimDateTime, but was {type(value)}")

    @pydantic.validator("time_increment", pre=True)  # type: ignore
    @classmethod
    def _validate_time_increment(cls, value: Any) -> TimeDelta:
        if isinstance(value, TimeDelta):
            return value
        elif isinstance(value, str):
            if match := re.fullmatch(r"^[0-9]+mo$", value):
                return TimeDelta(months=int(match.group(0)[:-2]))
            elif match := re.fullmatch(r"^[0-9]+hr$", value):
                return TimeDelta(hours=int(match.group(0)[:-2]))
            elif match := re.fullmatch(r"^[0-9]+yr$", value):
                return TimeDelta(years=int(match.group(0)[:-2]))
            elif match := re.fullmatch(r"^[0-9]+dy$", value):
                return TimeDelta(days=int(match.group(0)[:-2]))
        elif isinstance(value, int):
            return TimeDelta(hours=value)
        raise TypeError(f"Expected str or DeltaTime, but was {type(value)}")

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**{**defaults.dict(), **data})

    class Config:
        arbitrary_types_allowed = True
