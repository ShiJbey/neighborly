from typing import Any

from neighborly.components.species import Species
from neighborly.core.ecs import IComponentFactory, World


class SpeciesFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Species:
        species_type: str = kwargs.get("species_type")
        return Species(
            world.gameobject_manager.create_component(species_type)
        )

