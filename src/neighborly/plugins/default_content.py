"""Content plugin with all built-in Neighborly content."""

from neighborly.plugins import (
    default_businesses,
    default_character_names,
    default_characters,
    default_settlement_names,
    default_settlements,
    default_systems,
    default_traits,
)
from neighborly.simulation import Simulation


def load_plugin(sim: Simulation) -> None:
    """Load plugin data."""

    default_businesses.load_plugin(sim)
    default_character_names.load_plugin(sim)
    default_characters.load_plugin(sim)
    default_settlement_names.load_plugin(sim)
    default_settlements.load_plugin(sim)
    default_systems.load_plugin(sim)
    default_traits.load_plugin(sim)
