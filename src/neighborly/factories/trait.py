import random
from typing import Any, List, Set, Type

from ordered_set import OrderedSet

from neighborly.components.trait import ITrait, TraitLibrary, Traits
from neighborly.core.ecs import IComponentFactory, World


class TraitsFactory(IComponentFactory):
    """Creates traits component and provides it a list of component types to create."""

    def create(self, world: World, **kwargs: Any) -> Traits:
        rng = world.resource_manager.get_resource(random.Random)
        trait_library = world.resource_manager.get_resource(TraitLibrary)
        trait_spec: List[str] = kwargs.get("traits", [])
        max_incidental: int = kwargs.get("max_incidental", 10)

        trait_types: OrderedSet[Type[ITrait]] = OrderedSet([])
        prohibited_traits: Set[Type[ITrait]] = set(
            [trait_library.get_trait_type(t) for t in kwargs.get("prohibited", [])]
        )

        # Process specified traits first
        for entry in trait_spec:
            if entry[0] == "?":
                trait_type = trait_library.get_trait_type(entry[1:])
                if trait_type not in prohibited_traits and rng.random() < 0.5:
                    trait_types.add(trait_type)
                    prohibited_traits.union(trait_type.get_conflicts())
            else:
                trait_choices = [
                    trait_library.get_trait_type(option.strip())
                    for option in entry.split("|")
                ]
                filtered_choices = [t for t in trait_choices if t not in prohibited_traits]
                if filtered_choices:
                    chosen_trait = rng.choice(filtered_choices)
                    trait_types.add(chosen_trait)
                    prohibited_traits.union(chosen_trait.get_conflicts())

        # Process incidental traits
        incidental_traits = [*trait_library.incidental_traits]
        if len(incidental_traits):
            incidental_traits_sample = rng.sample(
                incidental_traits, k=min(len(incidental_traits), max_incidental)
            )

            for trait_type in incidental_traits_sample:
                if trait_type in prohibited_traits:
                    continue

                if rng.random() < trait_type.incidence_probability():
                    trait_types.add(trait_type)
                    prohibited_traits.union(trait_type.get_conflicts())

        return Traits(trait_types)
