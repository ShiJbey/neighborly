"""Simulation configuration.

"""

from __future__ import annotations

import random
from typing import Union

import pydantic


class LoggingConfig(pydantic.BaseModel):
    """Configuration settings for logging within a simulation."""

    logging_enabled: bool = True
    """Toggles if logging messages are sent anywhere."""

    log_level: str = "INFO"
    """The logging level to use."""

    log_file_path: str = "./neighborly.log"
    """Toggles if logging output should be save to this file name in log_directory."""

    log_to_terminal: bool = True
    """Toggles if logs should be printed to the terminal or saved to a file."""


class SimulationConfig(pydantic.BaseModel):
    """Configuration settings for a Simulation instance."""

    seed: Union[str, int] = pydantic.Field(
        default_factory=lambda: random.randint(0, 9999999)
    )
    """Value used for pseudo-random number generation."""

    logging: LoggingConfig = pydantic.Field(default_factory=LoggingConfig)
    """Configuration settings for logging."""

    settlement_with_id: str = ""
    """Settlement definition ID to instantiate during simulation initialization."""

    settlement_with_tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to use to select a settlement definition to instantiate."""
