"""Utility functions for working with Location GameObjects.

"""
from neighborly import GameObject
from neighborly.components.shared import FrequentedBy, FrequentedLocations, Location


def add_sub_location(parent_location: GameObject, sub_location: GameObject) -> None:
    """Adds a location as a child of another location.

    Parameters
    ----------
    parent_location
        The location to add a child to.
    sub_location
        The new location to add.
    """
    parent_location.get_component(Location).children.add(sub_location)
    sub_location.get_component(Location).parent = parent_location
    parent_location.add_child(sub_location)


def remove_sub_location(parent_location: GameObject, sub_location: GameObject) -> None:
    """Removes a location as a child of another location.

    Parameters
    ----------
    parent_location
        The location to add a child to.
    sub_location
        The new location to add.
    """
    parent_location.get_component(Location).children.remove(sub_location)
    sub_location.get_component(Location).parent = None
    parent_location.remove_child(sub_location)


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
