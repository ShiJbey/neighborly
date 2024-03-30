"""Helper functions for working with locations.

"""

from repraxis.query import DBQuery

from neighborly.components.location import (
    FrequentedLocations,
    Location,
    LocationPreferenceRule,
    LocationPreferences,
)
from neighborly.ecs import GameObject
from neighborly.libraries import LocationPreferenceLibrary


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


def check_location_preference_preconditions(
    rule: LocationPreferenceRule, character: GameObject, location: GameObject
) -> float:
    """Check all preconditions and return a weight modifier.

    Parameters
    ----------
    gameobject
        A location to score.

    Returns
    -------
    float
        A probability score from [0.0, 1.0] of the character frequenting the
        location. Or -1 if it does not pass the preconditions.
    """

    result = DBQuery([rule.preconditions]).run(
        character.world.rp_db, [{"?location": location.uid, "?subject": character.uid}]
    )

    return result.success


def score_location(character: GameObject, location: GameObject) -> float:
    """Calculate a score for a character choosing to frequent this location.

    Parameters
    ----------
    location
        A location to score

    Returns
    -------
    float
        A probability score from [0.0, 1.0]
    """

    library = character.world.resource_manager.get_resource(LocationPreferenceLibrary)
    rules = character.get_component(LocationPreferences).rules

    cumulative_score: float = 0.5
    consideration_count: int = 1

    for rule_id in rules:
        rule = library.rules[rule_id]
        if check_location_preference_preconditions(rule, character, location):
            consideration_score = rule.probability
        else:
            consideration_score = -1

        # Scores greater than zero are added to the cumulative score
        if consideration_score > 0:
            cumulative_score += consideration_score
            consideration_count += 1

        # Scores equal to zero make the entire score zero (make zero a veto value)
        elif consideration_score == 0.0:
            cumulative_score = 0.0
            break

    # Scores are averaged using the arithmetic mean
    final_score = cumulative_score / consideration_count

    return final_score


def add_location_preference(character: GameObject, rule_id: str) -> None:
    """Add a location preference to a character."""

    character.get_component(LocationPreferences).add_rule(rule_id)


def remove_location_preference(character: GameObject, rule_id: str) -> bool:
    """Remove a location preference from a character."""

    return character.get_component(LocationPreferences).remove_rule(rule_id)
