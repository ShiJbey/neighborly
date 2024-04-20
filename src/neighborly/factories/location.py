"""Factories for location components.

"""

from typing import Any

from neighborly.components.location import (
    FrequentedLocations,
    Location,
    LocationPreferences,
)
from neighborly.ecs import Component, ComponentFactory, GameObject


class LocationFactory(ComponentFactory):
    """Creates instances of Location components."""

    __component__ = "Location"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return Location(gameobject, is_private=kwargs.get("is_private", False))


class FrequentedLocationsFactory(ComponentFactory):
    """Creates instances of FrequentedLocations components."""

    __component__ = "FrequentedLocations"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return FrequentedLocations(gameobject)


class LocationPreferencesFactory(ComponentFactory):
    """Creates instances of LocationPreferences components."""

    __component__ = "LocationPreferences"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return LocationPreferences(gameobject)
