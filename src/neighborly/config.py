from __future__ import annotations

import os
import random
from typing import Any, Dict, List, Optional, Tuple, Union

import pydantic


class PluginConfig(pydantic.BaseModel):
    """Settings for loading and constructing a plugin."""

    name: str
    """Name of the plugin's python module."""

    path: str = pydantic.Field(default_factory=lambda: os.getcwd())
    """The path where the plugin is located."""


class LoggingConfig(pydantic.BaseModel):
    """Configuration settings for logging within a simulation."""

    logging_enabled: bool = True
    """Toggles if logging messages are sent anywhere."""

    log_directory: str = "./logs"
    """The directory to save logs to when saving to file."""

    log_level: str = "INFO"
    """The logging level to use."""

    log_file_name: Optional[str] = None
    """Toggles if logging output should be save to this file name in log_directory."""


class NeighborlyConfig(pydantic.BaseModel):
    """Configuration settings for a Neighborly simulation instance."""

    seed: Union[str, int] = pydantic.Field(
        default_factory=lambda: random.randint(0, 9999999)
    )
    """A value used to seed the random number generator."""

    settlement_name: str = "#settlement_name#"
    """The name of the simulated settlement."""

    world_size: Tuple[int, int] = (5, 5)
    """The X/Y dimensions of the world in."""

    plugins: List[PluginConfig] = pydantic.Field(default_factory=list)
    """Plugins to import before running the simulation."""

    years_to_simulate: int = 50
    """The number of years to simulate. This is mainly used by the CLI."""

    logging: LoggingConfig = pydantic.Field(default_factory=LoggingConfig)
    """Configuration settings for logging."""

    settings: Dict[str, Any] = pydantic.Field(default_factory=dict)
    """Miscellaneous keyword settings."""

    # noinspection PyNestedDecorators
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

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**{**defaults.dict(), **data})

    class Config:
        arbitrary_types_allowed = True
