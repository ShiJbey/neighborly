"""Helper functions for working with locations.

"""

from neighborly.components.location import FrequentedBy, FrequentedLocations
from neighborly.ecs import GameObject


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
    location.get_component(FrequentedBy).add_character(character)


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
    location.get_component(FrequentedBy).remove_character(character)


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
        location.get_component(FrequentedBy).remove_character(character)
        frequented_locations_data.remove_location(location)


def remove_all_frequenting_characters(location: GameObject) -> None:
    """Remove all characters from frequenting the given location.

    Parameters
    ----------
    location
        A location.
    """
    frequented_by_data = location.get_component(FrequentedBy)
    characters = list(frequented_by_data)
    for character in characters:
        character.get_component(FrequentedLocations).remove_location(location)
        frequented_by_data.remove_character(character)


def score_location(self, location: GameObject) -> float:
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

    cumulative_score: float = 0.5
    consideration_count: int = 1

    for rule in self._rules:
        if rule.check_preconditions(location):
            consideration_score = rule.score

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
