import os
from pathlib import Path
from typing import Any, Dict, List

from neighborly.core.business import BusinessDefinition, OccupationDefinition
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.systems import LifeEventSystem
from neighborly.core.relationship import RelationshipModifier
from neighborly.loaders import YamlDataLoader, load_names
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

from neighborly.simulation import PluginContext

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


@YamlDataLoader.section_loader("Activities")
def _load_activity_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process data related to defining activities"""
    for activity in data:
        register_activity(Activity(activity["name"], trait_names=activity["traits"]))


def setup(ctx: PluginContext, **kwargs) -> None:
    # RelationshipModifier.register_tag(FriendModifier())

    # LifeEventProcessor.register_event(DeathEvent())
    # LifeEventProcessor.register_event(BecameChildEvent())
    # LifeEventProcessor.register_event(BecameAdolescentEvent())
    # LifeEventProcessor.register_event(BecameYoungAdultEvent())
    # LifeEventProcessor.register_event(BecameAdultEvent())
    # LifeEventProcessor.register_event(BecameSeniorEvent())
    # LifeEventProcessor.register_event(StartedDatingEvent())
    # LifeEventProcessor.register_event(DatingBreakUpEvent())
    # LifeEventProcessor.register_event(UnemploymentEvent())
    # LifeEventProcessor.register_event(BecameBusinessOwnerEvent())

    # ctx.world.add_system(DatingStatus.system_fn, 1)
    # ctx.world.add_system(MarriedStatus.system_fn, 1)
    # ctx.world.add_system(UnemployedStatus.system_fn, 1)
    # ctx.world.add_system(SocializeProcessor(), 2)

    # BusinessDefinition.register_type(restaurant_type)
    # BusinessDefinition.register_type(bar_type)
    # BusinessDefinition.register_type(department_store_type)

    # OccupationDefinition.register_type(manager_type)
    # OccupationDefinition.register_type(sales_associate_type)
    # OccupationDefinition.register_type(cashier_type)
    # OccupationDefinition.register_type(dj_type)
    # OccupationDefinition.register_type(bartender_type)
    # OccupationDefinition.register_type(security_type)
    # OccupationDefinition.register_type(cook_type)
    # OccupationDefinition.register_type(owner_type)
    # OccupationDefinition.register_type(proprietor_type)

    # Load character name data
    load_names("last_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt")
    load_names("first_name", filepath=_RESOURCES_DIR / "names" / "neutral_names.txt")
    load_names(
        "feminine_first_name",
        filepath=_RESOURCES_DIR / "names" / "feminine_names.txt",
    )
    load_names(
        "masculine_first_name",
        filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

    # Load potential names for different structures in the town
    load_names(
        "restaurant_name",
        filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt",
    )
    load_names("bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt")

    # Load potential names for the town
    load_names(
        "town_name", filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt"
    )

    # Load additional data from yaml
    # YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(ctx.engine)
