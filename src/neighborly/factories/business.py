from __future__ import annotations

from typing import Any, Dict, Type, cast

from neighborly.components.business import Business, Occupation, Services
from neighborly.core.ecs import IComponentFactory, World


class ServicesFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Services:
        return Services(kwargs.get("services", []))


class BusinessFactory(IComponentFactory):
    """Constructs instances of Business components"""

    def create(self, world: World, **kwargs: Any) -> Business:
        owner_type: str = kwargs["owner_type"]
        employee_positions: Dict[str, int] = kwargs.get("employee_types", {})

        return Business(
            owner_type=cast(
                Type[Occupation],
                world.gameobject_manager.get_component_info(owner_type).component_type,
            ),
            employee_types={
                cast(
                    Type[Occupation],
                    world.gameobject_manager.get_component_info(
                        employee_type
                    ).component_type,
                ): employee_count
                for employee_type, employee_count in employee_positions.items()
            },
        )
