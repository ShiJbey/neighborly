"""Trait Component Factories.

"""

# import random
from typing import Any

from neighborly.components.traits import Traits
from neighborly.ecs import Component, ComponentFactory, GameObject


class TraitsFactory(ComponentFactory):
    """Creates Traits component instances."""

    __component__ = "Traits"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        # rng = gameobject.world.resources.get_resource(random.Random)
        traits = Traits(gameobject)

        # starting_traits: list[dict[str, Any]] = kwargs.get("traits", [])

        # for entry in starting_traits:
        #     if trait_id := entry.get("with_id"):
        #         add_trait(character, trait_id)
        #     elif entry.with_tags:
        #         potential_traits = trait_library.get_definition_with_tags(
        #             entry.with_tags
        #         )

        #         trait_ids: list[str] = []
        #         trait_weights: list[int] = []

        #         for trait_def in potential_traits:
        #             if trait_def.spawn_frequency >= 1:
        #                 trait_ids.append(trait_def.definition_id)
        #                 trait_weights.append(trait_def.spawn_frequency)

        #         if len(trait_ids) == 0:
        #             continue

        #         chosen_trait = rng.choices(
        #             population=trait_ids, weights=trait_weights, k=1
        #         )[0]

        #         add_trait(gameobject, chosen_trait)

        return traits
