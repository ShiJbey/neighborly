from __future__ import annotations

from typing import Any, Dict, List

import pydantic

from .ecs import GameObject, World


class EntityPrefab(pydantic.BaseModel):
    """Configuration data for creating a new entity and any children

    Attributes
    ----------
    components: Dict[str, Dict[str, Any]]
        Configuration data for components to construct with the prefab mapped
        to the name of the component
    children: List[EntityPrefab]
        Information about child prefabs to instantiate along with this one
    """

    components: Dict[str, Dict[str, Any]] = pydantic.Field(default_factory=dict)
    children: List[EntityPrefab] = pydantic.Field(default_factory=list)

    def spawn(self, world: World) -> GameObject:
        """Spawn the prefab into the world and return the root-level entity

        Parameters
        ----------
        world: World
            The World instance to spawn this prefab into

        Returns
        -------
        GameObject
            A reference to the spawned entity
        """

        # spawn the root gameobject
        gameobject = world.spawn_gameobject()

        for component_name, component_data in self.components.items():
            try:
                gameobject.add_component(
                    world.get_component_info(component_name).factory.create(
                        world, **component_data
                    )
                )
            except KeyError:
                raise Exception(
                    f"Cannot find component, {component_name}. "
                    "Please ensure that this component has "
                    "been registered with the simulation's world instance."
                )

        for child in self.children:
            gameobject.add_child(child.spawn(world))

        return gameobject


EntityPrefab.update_forward_refs()
