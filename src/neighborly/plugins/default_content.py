"""Content plugin with all built-in Neighborly content."""

from neighborly.plugins import (
    default_behavior_systems,
    default_businesses,
    default_character_names,
    default_characters,
    default_considerations,
    default_effects,
    default_event_responses,
    default_preconditions,
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
    default_behavior_systems.load_plugin(sim)
    default_traits.load_plugin(sim)
    default_considerations.load_plugin(sim)
    default_event_responses.load_plugin(sim)
    default_effects.load_plugin(sim)
    default_preconditions.load_plugin(sim)
