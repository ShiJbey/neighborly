"""
samples/location_preference_rules.py

This sample shows how location preference rules are used to create probability distribution
of where a character may frequent within a town. LocationPreferenceRules are can be imported
from plugins and authored within the same script.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from neighborly import Component, GameObject, Neighborly
from neighborly.components.business import Services, ServiceType
from neighborly.components.shared import Location
from neighborly.core.ecs import TagComponent
from neighborly.decorators import component, location_preference_rule
from neighborly.utils.common import (
    calculate_location_probabilities,
    location_has_services,
)

sim = Neighborly()


@component(sim.world)
@dataclass
class Actor(Component):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@component(sim.world)
class SocialButterfly(TagComponent):
    pass


@component(sim.world)
class HealthNut(TagComponent):
    pass


@component(sim.world)
class BookWorm(TagComponent):
    pass


@component(sim.world)
class RecoveringAlcoholic(TagComponent):
    pass


@component(sim.world)
class Shopaholic(TagComponent):
    pass


@location_preference_rule(sim.world, "social-butterfly")
def social_butterfly_rule(
    character: GameObject, location: GameObject
) -> Optional[float]:
    if character.has_component(SocialButterfly) and location_has_services(
        location, ServiceType.Socializing
    ):
        return 1.0


@location_preference_rule(sim.world, "recovering-alcoholic")
def recovering_alcoholic_rule(
    character: GameObject, location: GameObject
) -> Optional[float]:
    if character.has_component(RecoveringAlcoholic) and location_has_services(
        location, ServiceType.Alcohol
    ):
        return 0.1


@location_preference_rule(sim.world, "shop-alcoholic")
def shopaholic_rule(character: GameObject, location: GameObject) -> Optional[float]:
    if character.has_component(Shopaholic) and location_has_services(
        location, ServiceType.Retail
    ):
        return 0.8


@location_preference_rule(sim.world, "book-worm")
def book_worm_rule(character: GameObject, location: GameObject) -> Optional[float]:
    if character.has_component(BookWorm) and location_has_services(
        location, ServiceType.Education
    ):
        return 0.8


@location_preference_rule(sim.world, "health-nut")
def rule(character: GameObject, location: GameObject) -> Optional[float]:
    if character.has_component(HealthNut) and location_has_services(
        location, ServiceType.Recreation
    ):
        return 0.8


def main():
    ###############################
    # SPAWN NEW LOCATIONS
    ###############################

    # We need to step the simulation once to create all the services
    sim.step()

    locations = [
        sim.world.gameobject_manager.spawn_gameobject(
            {
                Location: {},
                Services: {"services": ["Recreation"]},
            },
            name="Gym",
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            {
                Location: {},
                Services: {"services": ["Education", "PublicService", "Leisure"]},
            },
            name="Library",
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            {
                Location: {},
                Services: {"services": ["Retail", "Socializing", "Food"]},
            },
            name="Mall",
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            {
                Location: {},
                Services: {"services": ["Food", "Entertainment", "Socializing"]},
            },
            name="Bar",
        ),
    ]

    characters = [
        sim.world.gameobject_manager.spawn_gameobject(
            {Actor: {"name": "Alice"}, HealthNut: {}, SocialButterfly: {}}
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            {Actor: {"name": "James"}, Shopaholic: {}, BookWorm: {}, HealthNut: {}}
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            {
                Actor: {"name": "Raven"},
                HealthNut: {},
                SocialButterfly: {},
                RecoveringAlcoholic: {},
            }
        ),
    ]

    for c in characters:
        # Score all the locations in the map
        probabilities = calculate_location_probabilities(c, locations)
        print(f"== {c.get_component(Actor).name} ==")
        print([(loc.name, prob) for prob, loc in probabilities])


if __name__ == "__main__":
    main()
