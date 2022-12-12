"""
test_loaders.py

Ensure that users can load custom configurations from YAML
"""
from dataclasses import dataclass
from typing import List

import pytest

from neighborly.core.ecs import Component
from neighborly.engine import NeighborlyEngine
from neighborly.plugins.defaults.archetypes import (
    BaseBusinessArchetype,
    BaseCharacterArchetype,
    BaseResidenceArchetype,
)


@dataclass
class Wealth(Component):
    money: int


class ComplexComponent(Component):
    def __init__(self, items: List[str]) -> None:
        super(Component, self).__init__()


@pytest.fixture
def sample_yaml_data() -> str:
    ...


@pytest.fixture
def sample_engine() -> NeighborlyEngine:
    engine = NeighborlyEngine()
    engine.character_archetypes.add(BaseCharacterArchetype())
    engine.business_archetypes.add(BaseBusinessArchetype())
    engine.residence_archetypes.add(BaseResidenceArchetype())

    return engine


def test_load_character_archetype(
    sample_engine: NeighborlyEngine, sample_yaml_data: str
) -> None:
    assert False


def test_load_business_archetype(
    ample_engine: NeighborlyEngine, sample_yaml_data: str
) -> None:
    assert False


def test_load_residence_archetype(
    ample_engine: NeighborlyEngine, sample_yaml_data: str
) -> None:
    assert False


def test_load_occupation_types(
    ample_engine: NeighborlyEngine, sample_yaml_data: str
) -> None:
    assert False
