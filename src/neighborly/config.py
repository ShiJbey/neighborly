"""Simulation configuration.

"""

from __future__ import annotations

import random
from typing import Union

import attrs


@attrs.define
class LoggingConfig:
    """Configuration settings for logging within a simulation."""

    logging_enabled: bool = True
    """Toggles if logging messages are sent anywhere."""

    log_level: str = "INFO"
    """The logging level to use."""

    log_file_path: str = "./neighborly.log"
    """Toggles if logging output should be save to this file name in log_directory."""

    log_to_terminal: bool = True
    """Toggles if logs should be printed to the terminal or saved to a file."""


@attrs.define
class SimulationConfig:
    """Configuration settings for a Simulation instance."""

    seed: Union[str, int] = attrs.field(factory=lambda: random.randint(0, 9999999))
    """Value used for pseudo-random number generation."""

    logging: LoggingConfig = attrs.field(factory=LoggingConfig)
    """Configuration settings for logging."""

    growth_factor: float = 0.5
    """Probability of a district spawning a new character."""

    num_districts: int = 4
    """The number of districts to generate in the settlement."""

    theme_tags: list[str] = attrs.field(factory=list)
    """Content tags to guide settlement development."""
