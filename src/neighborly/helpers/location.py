"""Helper functions for working with locations.

"""

from neighborly.components.location import (
    FrequentedLocations,
    Location,
    LocationPreferences,
)
from neighborly.components.stats import Stat
from neighborly.ecs import GameObject
from neighborly.effects.modifiers import StatModifier


def add_frequented_location(character: GameObject, location: GameObject) -> None:
    """Add a location to a character's collection of frequented locations.

    Parameters
    ----------
    character
        A character.
    location
        A location.
    """
    character.get_component(FrequentedLocations).add_location(location)
    location.get_component(Location).add_character(character)


def remove_frequented_location(character: GameObject, location: GameObject) -> None:
    """Remove a location from a character's collection of frequented locations.

    Parameters
    ----------
    character
        A character.
    location
        A location.
    """
    character.get_component(FrequentedLocations).remove_location(location)
    location.get_component(Location).remove_character(character)


def remove_all_frequented_locations(character: GameObject) -> None:
    """Remove all frequented locations from the character.

    Parameters
    ----------
    character
        A character.
    """
    frequented_locations_data = character.get_component(FrequentedLocations)
    locations = list(frequented_locations_data)
    for location in locations:
        location.get_component(Location).remove_character(character)
        frequented_locations_data.remove_location(location)


def remove_all_frequenting_characters(location: GameObject) -> None:
    """Remove all characters from frequenting the given location.

    Parameters
    ----------
    location
        A location.
    """
    frequented_by_data = location.get_component(Location)
    characters = list(frequented_by_data)
    for character in characters:
        character.get_component(FrequentedLocations).remove_location(location)
        frequented_by_data.remove_character(character)


def score_location(character: GameObject, location: GameObject) -> float:
    """Calculate a score for a character choosing to frequent this location.

    Parameters
    ----------
    character
        The character scoring the location.
    location
        A location to score.

    Returns
    -------
    float
        A probability score from [0.0, 1.0].
    """
    preferences = character.get_component(LocationPreferences).preferences

    score = Stat(base_value=0.5, bounds=(0.0, 1.0))

    for preference in preferences:
        if all(p.check(location) for p in preference.location_preconditions) and all(
            p.check(character) for p in preference.character_preconditions
        ):
            score.add_modifier(
                StatModifier(
                    stat="",
                    value=preference.value,
                    modifier_type=preference.modifier_type,
                )
            )

    # Scores are averaged using the arithmetic mean
    final_score = score.value

    return final_score
