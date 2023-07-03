from __future__ import annotations

from typing import Any, Dict

from neighborly.components.business import (
    Business,
    JobRequirementParser,
    JobRequirements,
    OccupationLibrary,
    ServiceLibrary,
    Services,
)
from neighborly.core.ecs import Component, GameObject, IComponentFactory, World


class ServicesFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Services:
        service_library = world.resource_manager.get_resource(ServiceLibrary)
        services = [
            service_library.get(service_name) for service_name in kwargs["services"]
        ]
        return Services(services)


class BusinessFactory(IComponentFactory):
    """Constructs instances of Business components"""

    def create(self, world: World, **kwargs: Any) -> Component:
        occupation_library = world.resource_manager.get_resource(OccupationLibrary)

        owner_type: str = kwargs["owner_type"]
        employee_types: Dict[GameObject, int] = {
            occupation_library.get(occupation_name): num_slots
            for occupation_name, num_slots in kwargs.get("employee_types", {}).items()
        }

        return Business(
            owner_type=occupation_library.get(owner_type),
            employee_types=employee_types,
        )


class JobRequirementsFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        rule_strings: list[str] = kwargs["rules"]

        parser = JobRequirementParser(world)

        rules = [parser.parse_string(entry) for entry in rule_strings]

        return JobRequirements(rules)
