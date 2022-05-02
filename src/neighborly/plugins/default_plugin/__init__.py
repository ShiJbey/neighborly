import os
from pathlib import Path

from neighborly.core.business import OccupationDefinition, BusinessDefinition
from neighborly.core.processors import LifeEventProcessor
from neighborly.core.relationship import RelationshipModifier
from neighborly.loaders import load_names, YamlDataLoader
from neighborly.plugins.default_plugin.businesses import (
    restaurant_type,
    bar_type,
    department_store_type,
    manager_type,
    sales_associate_type,
    cashier_type,
    dj_type,
    bartender_type,
    security_type,
    cook_type,
    owner_type,
    proprietor_type,
)
from neighborly.plugins.default_plugin.events import (
    DeathEvent,
    BecameAdultEvent,
    BecameSeniorEvent,
    StartedDatingEvent,
    DatingBreakUpEvent,
    UnemploymentEvent,
    BecameBusinessOwnerEvent,
    BecameChildEvent,
    BecameYoungAdultEvent,
    BecameAdolescentEvent,
)
from neighborly.plugins.default_plugin.relationship_modifiers import FriendModifier
from neighborly.plugins.default_plugin.statuses import (
    DatingStatus,
    MarriedStatus,
    UnemployedStatus,
)
from neighborly.simulation import PluginContext

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


def setup(ctx: PluginContext, **kwargs) -> None:
    RelationshipModifier.register_tag(FriendModifier())

    LifeEventProcessor.register_event(DeathEvent())
    LifeEventProcessor.register_event(BecameChildEvent())
    LifeEventProcessor.register_event(BecameAdolescentEvent())
    LifeEventProcessor.register_event(BecameYoungAdultEvent())
    LifeEventProcessor.register_event(BecameAdultEvent())
    LifeEventProcessor.register_event(BecameSeniorEvent())
    LifeEventProcessor.register_event(StartedDatingEvent())
    LifeEventProcessor.register_event(DatingBreakUpEvent())
    LifeEventProcessor.register_event(UnemploymentEvent())
    LifeEventProcessor.register_event(BecameBusinessOwnerEvent())

    ctx.world.add_system(DatingStatus.system_fn, 1)
    ctx.world.add_system(MarriedStatus.system_fn, 1)
    ctx.world.add_system(UnemployedStatus.system_fn, 1)

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
    YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(ctx.engine)
