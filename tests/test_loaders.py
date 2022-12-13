"""
test_loaders.py

Ensure that users can load custom configurations from YAML
"""
import os
import pathlib
from dataclasses import dataclass

import pytest

from neighborly.components.character import GameCharacter, Gender, GenderValue
from neighborly.core.ecs import Component
from neighborly.loaders import NeighborlyYamlImporter, load_character_archetypes
from neighborly.plugins.defaults import names
from neighborly.plugins.defaults.archetypes import (
    BaseBusinessArchetype,
    BaseCharacterArchetype,
    BaseResidenceArchetype,
)
from neighborly.simulation import Neighborly, Simulation


@dataclass
class Wealth(Component):
    money: int


@pytest.fixture
def simulation() -> Simulation:
    sim = Neighborly().add_plugin(names.get_plugin()).build()
    sim.engine.character_archetypes.add(BaseCharacterArchetype())
    sim.engine.business_archetypes.add(BaseBusinessArchetype())
    sim.engine.residence_archetypes.add(BaseResidenceArchetype())
    sim.engine.register_component(Wealth)
    return sim


def test_load_data_from_str(simulation: Simulation) -> None:
    """Ensure that data can be read from an in-code yaml string"""
    yaml_data = """
        Characters:
            -
                name: "Human:wealthy"
                spawn_config:
                    spouse_archetypes:
                        - "Human:*"
                    chance_spawn_with_spouse: 0.7
                    max_children_at_spawn: 3
                    child_archetypes:
                        - "Human:*"
                    spawn_frequency: 0.8
                base: BaseCharacter
                options:
                    components:
                        -
                            name: Wealth
                            options:
                                money: 10000
        """

    NeighborlyYamlImporter.from_str(yaml_data).load(
        simulation, [load_character_archetypes]
    )

    archetype = simulation.engine.character_archetypes.get("Human:wealthy")

    gameobject = archetype.spawn(simulation.world)

    assert gameobject.has_component(Wealth)
    assert gameobject.get_component(Wealth).money == 10000
    assert gameobject.has_component(GameCharacter)


def test_load_data_from_file(simulation: Simulation) -> None:
    NeighborlyYamlImporter.from_path(
        pathlib.Path(os.path.abspath(__file__)).parent / "data" / "loader_data.yaml"
    ).load(simulation, [load_character_archetypes])

    archetype = simulation.engine.character_archetypes.get("Human:male")

    gameobject = archetype.spawn(simulation.world)

    assert gameobject.has_component(Wealth)
    assert gameobject.get_component(Wealth).money == 5000
    assert gameobject.has_component(GameCharacter)
    assert gameobject.get_component(Gender).value == GenderValue.Male
