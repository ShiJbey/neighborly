import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from neighborly.core.business import (
    BusinessDefinition,
    BusinessFactory,
    OccupationDefinition,
)
from neighborly.core.character import GameCharacterFactory
from neighborly.core.engine import (
    ComponentDefinition,
    EntityArchetypeDefinition,
    NeighborlyEngine,
)
from neighborly.core.life_event import LifeEventLogger
from neighborly.core.location import LocationFactory
from neighborly.core.name_generation import TraceryNameFactory
from neighborly.core.position import Position2DFactory
from neighborly.core.residence import ResidenceFactory
from neighborly.core.routine import RoutineFactory
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.systems import (
    AddResidentsSystem,
    LifeEventSystem,
    RoutineSystem,
    TimeSystem,
)
from neighborly.loaders import YamlDataLoader
from neighborly.plugins.default_plugin.activity import Activity, register_activity
from neighborly.plugins.default_plugin.businesses import (
    bar_type,
    bartender_type,
    cashier_type,
    cook_type,
    department_store_type,
    dj_type,
    manager_type,
    owner_type,
    proprietor_type,
    restaurant_type,
    sales_associate_type,
    security_type,
)
from neighborly.simulation import Plugin, Simulation

# from neighborly.plugins.default_plugin.events import (
#     BecameAdolescentEvent,
#     BecameAdultEvent,
#     BecameBusinessOwnerEvent,
#     BecameChildEvent,
#     BecameSeniorEvent,
#     BecameYoungAdultEvent,
#     DatingBreakUpEvent,
#     DeathEvent,
#     StartedDatingEvent,
#     UnemploymentEvent,
# )

logger = logging.getLogger(__name__)

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


@YamlDataLoader.section_loader("Activities")
def _load_activity_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process data related to defining activities"""
    for entry in data:
        register_activity(Activity(entry["name"], trait_names=entry["traits"]))


def initialize_tracery_name_factory() -> TraceryNameFactory:
    name_factory = TraceryNameFactory()

    # Load character name data
    name_factory.load_names(
        rule_name="last_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt"
    )
    name_factory.load_names(
        rule_name="first_name", filepath=_RESOURCES_DIR / "names" / "neutral_names.txt"
    )
    name_factory.load_names(
        rule_name="feminine_first_name",
        filepath=_RESOURCES_DIR / "names" / "feminine_names.txt",
    )
    name_factory.load_names(
        rule_name="masculine_first_name",
        filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

    # Load potential names for different structures in the town
    name_factory.load_names(
        rule_name="restaurant_name",
        filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt",
    )
    name_factory.load_names(
        rule_name="bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt"
    )

    # Load potential names for the town
    name_factory.load_names(
        rule_name="town_name",
        filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
    )

    return name_factory


class DefaultPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        # Add default factories
        sim.get_engine().add_component_factory(GameCharacterFactory())
        sim.get_engine().add_component_factory(RoutineFactory())
        sim.get_engine().add_component_factory(LocationFactory())
        sim.get_engine().add_component_factory(ResidenceFactory())
        sim.get_engine().add_component_factory(Position2DFactory())
        sim.get_engine().add_component_factory(BusinessFactory())

        # Add default systems
        sim.world.add_system(TimeSystem(kwargs.get("days_per_year", 10)), 10)
        sim.world.add_system(RoutineSystem(), 5)
        sim.world.add_system(LifeEventSystem())
        sim.world.add_system(AddResidentsSystem())

        # Add default resources
        sim.add_resource(RelationshipNetwork())
        sim.add_resource(LifeEventLogger())
        sim.add_resource(initialize_tracery_name_factory())

        # LifeEventProcessor.register_event(DeathEvent())
        # LifeEventProcessor.register_event(StartedDatingEvent())
        # LifeEventProcessor.register_event(DatingBreakUpEvent())
        # LifeEventProcessor.register_event(UnemploymentEvent())
        # LifeEventProcessor.register_event(BecameBusinessOwnerEvent())

        BusinessDefinition.register_type(restaurant_type)
        BusinessDefinition.register_type(bar_type)
        BusinessDefinition.register_type(department_store_type)

        OccupationDefinition.register_type(manager_type)
        OccupationDefinition.register_type(sales_associate_type)
        OccupationDefinition.register_type(cashier_type)
        OccupationDefinition.register_type(dj_type)
        OccupationDefinition.register_type(bartender_type)
        OccupationDefinition.register_type(security_type)
        OccupationDefinition.register_type(cook_type)
        OccupationDefinition.register_type(owner_type)
        OccupationDefinition.register_type(proprietor_type)

        sim.get_engine().add_residence_archetype(
            EntityArchetypeDefinition(
                name="House",
                components={
                    "Residence": ComponentDefinition(
                        component_type="Residence",
                    ),
                    "Location": ComponentDefinition(
                        component_type="Location",
                    ),
                },
            )
        )
        # Load additional data from yaml
        # YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(ctx.engine)
