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
