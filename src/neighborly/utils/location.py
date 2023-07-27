"""Utility functions for working with Location GameObjects.

"""
from neighborly import GameObject
from neighborly.components.shared import FrequentedBy, FrequentedLocations


def add_frequented_location(character: GameObject, location: GameObject) -> None:
    """Add a location to a character's set of frequented locations."""
    character.get_component(FrequentedLocations).add(location)
    location.get_component(FrequentedBy).add(character)


def remove_frequented_location(character: GameObject, location: GameObject) -> None:
    """Remove a location from a character's set of frequented locations."""
    frequented_locations = character.get_component(FrequentedLocations)
    frequented_by = location.get_component(FrequentedBy)

    if location in frequented_locations:
        frequented_locations.remove(location)

    if character in frequented_by:
        frequented_by.remove(character)
