"""
This is another attempt at improving the entity generation process. As I have gained
a better understanding of how I should model characters, it has helped realize the
problems with previous interfaces. For this iteration, we are breaking apart the pieces
of characters into more individual components and placing probabilities on those
components being present at spawn-time.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Type, Union

from neighborly.builtin.components import CanGetPregnant, Gender, GenderValue
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.simulation import SimulationBuilder


class Actor(Component):
    pass


class Shape(Component):
    def __init__(self, shape_type: str) -> None:
        super().__init__()
        self.shape_type: str = shape_type


class Color(Component):
    def __init__(self, color: str) -> None:
        super().__init__()
        self.color: str = color

    @classmethod
    def create(cls, world: World, **kwargs) -> Component:
        color_frequencies = [("red", 1), ("blue", 1), ("yellow", 1), ("green", 1)]
        options, weights = tuple(zip(*color_frequencies))
        choice: str = world.get_resource(NeighborlyEngine).rng.choices(
            options, weights=weights
        )[0]

        return Color(choice)


class LongHair(Component):
    pass


class Popular(Component):
    pass


class LargeLeftEar(Component):
    pass


class ComponentProbabilityFn(Protocol):
    def __call__(self, world: World, gameobject: GameObject) -> float:
        raise NotImplementedError


def const_prob(probability: float):
    def probability_fn(world: World, gameobject: GameObject) -> float:
        return probability

    return probability_fn


@dataclass
class ArchetypeEntry:
    component_type: Type[Component]
    probability: ComponentProbabilityFn
    options: Dict[str, Any]


class AdvancedArchetype:
    def __init__(self) -> None:
        self.components: List[ArchetypeEntry] = []

    def add_component(
        self,
        component_type: Type[Component],
        probability: Union[float, ComponentProbabilityFn] = 1.0,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.components.append(
            ArchetypeEntry(
                component_type,
                const_prob(probability) if type(probability) == float else probability,
                options if options else {},
            )
        )


def can_get_pregnant_based_on_gender(world: World, gameobject: GameObject) -> float:
    if gameobject.has_component(Gender):
        gender = gameobject.get_component(Gender)
        if gender.gender == GenderValue.Female:
            return 0.8
        if gender.gender == GenderValue.Male:
            return 0.0
    return 0.5


def main():
    aa_0 = AdvancedArchetype()
    aa_0.add_component(Actor)
    aa_0.add_component(Gender)
    aa_0.add_component(CanGetPregnant, probability=can_get_pregnant_based_on_gender)
    aa_0.add_component(Popular, 0.5)
    aa_0.add_component(LongHair, 0.3)
    aa_0.add_component(LargeLeftEar, 0.1)

    sim = SimulationBuilder().build()

    go = sim.world.spawn_gameobject()
    rng = sim.world.get_resource(NeighborlyEngine).rng
    for entry in aa_0.components:
        if rng.random() < entry.probability(sim.world, go):
            go.add_component(entry.component_type.create(sim.world, **entry.options))

    print(go.components)


if __name__ == "__main__":
    main()
