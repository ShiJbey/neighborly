from __future__ import annotations

from typing import Any, List, Optional

from neighborly.components.shared import FrequentedLocations, Location, Name
from neighborly.core.ecs import IComponentFactory, World
from neighborly.core.tracery import Tracery


class NameFactory(IComponentFactory):
    """Creates instances of Name Components using Tracery"""

    def create(self, world: World, name: str = "", **kwargs: Any) -> Name:
        name_generator = world.get_resource(Tracery)
        return Name(name_generator.generate(name))


class FrequentedLocationsFactory(IComponentFactory):
    """Factory that create Location component instances"""

    def create(
        self, world: World, locations: Optional[List[int]] = None, **kwargs: Any
    ) -> FrequentedLocations:
        return FrequentedLocations(set(locations if locations else []))


class LocationFactory(IComponentFactory):
    """Factory that create Location component instances"""

    def create(
        self, world: World, activities: Optional[List[str]] = None, **kwargs: Any
    ) -> Location:
        return Location()
