import os
from pathlib import Path

from neighborly.core.business import OccupationType, BusinessType
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.processors import LifeEventProcessor
from neighborly.core.relationship import RelationshipTag
from neighborly.core.status import StatusType
from neighborly.loaders import load_names, YamlDataLoader
from neighborly.plugins.default_plugin.businesses import restaurant_type, bar_type, department_store_type, \
    manager_type, sales_associate_type, cashier_type, dj_type, bartender_type, security_type, cook_type, owner_type, \
    proprietor_type
from neighborly.plugins.default_plugin.events import DeathEvent, BecameAdultEvent, BecameSeniorEvent, \
    StartedDatingEvent, DatingBreakUpEvent, BecameUnemployedEvent, BecameBusinessOwnerEvent
from neighborly.plugins.default_plugin.relationship_tags import FriendTag
from neighborly.plugins.default_plugin.statuses import AdultStatusType, SeniorStatusType, DatingStatusType, \
    MarriedStatusType, UnemployedStatusType

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


def initialize_plugin(engine: NeighborlyEngine) -> None:
    # Load character name data
    load_names("last_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt")
    load_names("first_name", filepath=_RESOURCES_DIR / "names" / "neutral_names.txt")
    load_names(
        "feminine_first_name", filepath=_RESOURCES_DIR / "names" / "feminine_names.txt"
    )
    load_names(
        "masculine_first_name",
        filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

    # Load potential names for different structures in the town
    load_names(
        "restaurant_name", filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt"
    )
    load_names("bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt")

    # Load potential names for the town
    load_names(
        "town_name",
        filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
    )

    YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(engine)

    RelationshipTag.register_tag(FriendTag())

    LifeEventProcessor.register_event(DeathEvent())
    LifeEventProcessor.register_event(BecameAdultEvent())
    LifeEventProcessor.register_event(BecameSeniorEvent())
    LifeEventProcessor.register_event(StartedDatingEvent())
    LifeEventProcessor.register_event(DatingBreakUpEvent())
    LifeEventProcessor.register_event(BecameUnemployedEvent())
    LifeEventProcessor.register_event(BecameBusinessOwnerEvent())

    StatusType.register_type(AdultStatusType())
    StatusType.register_type(SeniorStatusType())
    StatusType.register_type(DatingStatusType())
    StatusType.register_type(MarriedStatusType())
    StatusType.register_type(UnemployedStatusType())

    BusinessType.register_type(restaurant_type)
    BusinessType.register_type(bar_type)
    BusinessType.register_type(department_store_type)

    OccupationType.register_type(manager_type)
    OccupationType.register_type(sales_associate_type)
    OccupationType.register_type(cashier_type)
    OccupationType.register_type(dj_type)
    OccupationType.register_type(bartender_type)
    OccupationType.register_type(security_type)
    OccupationType.register_type(cook_type)
    OccupationType.register_type(owner_type)
    OccupationType.register_type(proprietor_type)
