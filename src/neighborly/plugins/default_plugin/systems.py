from logging import getLogger
from typing import Dict, List, Optional

from neighborly.core.business import BusinessDefinition
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship, RelationshipModifier
from neighborly.core.residence import Residence
from neighborly.core.rng import DefaultRNG
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import SimDateTime
from neighborly.core.town import Town

logger = getLogger(__name__)


class CityPlanner:
    """Responsible for adding residents to the town"""

    def __init__(self, weights: Optional[Dict[str, int]] = None):
        self.weights: Dict[str, int] = {}
        if weights:
            self.weights.update(weights)

    def __call__(self, world: World, **kwargs):
        self.try_add_business(world)

    def try_add_business(self, world: World) -> None:
        town = world.get_resource(Town)
        engine = world.get_resource(NeighborlyEngine)

        # Get eligible businesses
        eligible_business_types = self.get_eligible_types(world)

        if not eligible_business_types:
            return

        business_type_to_build = (
            world.get_resource(DefaultRNG).choice(eligible_business_types).name
        )

        if town.layout.has_vacancy():
            engine.filter_place_archetypes({"includes": []})
            place = engine.spawn_business(business_type_to_build)
            town.layout.reserve_space(place.id)
            world.add_gameobject(place)
            logger.debug(f"Added business {place}")

    @classmethod
    def get_eligible_types(cls, world: World) -> List["BusinessDefinition"]:
        """
        Return all business types that may be built
        given the state of the simulation
        """
        population = world.get_resource(Town).population
        engine = world.get_resource(NeighborlyEngine)

        eligible_types: List["BusinessDefinition"] = []

        for t in BusinessDefinition.get_all_types():
            if t.instances >= t.max_instances:
                continue

            if population < t.min_population:
                continue

            try:
                engine.get_business_archetype(t.name)
            except KeyError:
                continue

            eligible_types.append(t)

        return eligible_types
