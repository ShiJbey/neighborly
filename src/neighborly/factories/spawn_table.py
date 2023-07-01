"""Factories for creating spawn tables.

"""

from typing import Any, Dict, List

from neighborly.components.spawn_table import (
    CharacterSpawnTable,
    BusinessSpawnTable,
    ResidenceSpawnTable,
)
from neighborly.core.ecs import IComponentFactory, World


class CharacterSpawnTableFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> CharacterSpawnTable:
        entries: List[Dict[str, Any]] = kwargs.get("entries", [])
        table = CharacterSpawnTable(entries)
        return table


class BusinessSpawnTableFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> BusinessSpawnTable:
        entries: List[Dict[str, Any]] = kwargs.get("entries", [])
        table = BusinessSpawnTable(entries)
        return table


class ResidenceSpawnTableFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> ResidenceSpawnTable:
        entries: List[Dict[str, Any]] = kwargs.get("entries", [])
        table = ResidenceSpawnTable(entries)
        return table
