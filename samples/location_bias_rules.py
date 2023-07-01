"""
samples/location_bias_rules.py

This sample shows how location bias rules are used to create probability distribution
of where a character may frequent within a town. LocationBiasRules are can be imported
from plugins and authored within the same script.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from neighborly import Component, GameObject, Neighborly
from neighborly.components.activity import (
    Activities,
    ActivityLibrary,
    register_activity_type,
)
from neighborly.components.shared import Location
from neighborly.core.ecs import GameObjectPrefab, TagComponent
from neighborly.decorators import component, location_bias_rule
from neighborly.utils.common import (
    calculate_location_probabilities,
    location_has_activities,
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


@location_bias_rule(sim.world, "social-butterfly")
def social_butterfly_rule(character: GameObject, location: GameObject) -> Optional[int]:
    if character.has_component(SocialButterfly) and location_has_activities(
        location, "Socializing"
    ):
        return 2


@location_bias_rule(sim.world, "recovering-alcoholic")
def recovering_alcoholic_rule(
    character: GameObject, location: GameObject
) -> Optional[int]:
    if character.has_component(RecoveringAlcoholic) and location_has_activities(
        location, "Drinking"
    ):
        return -3


@location_bias_rule(sim.world, "shop-alcoholic")
def shopaholic_rule(character: GameObject, location: GameObject) -> Optional[int]:
    if character.has_component(Shopaholic) and location_has_activities(
        location, "Shopping"
    ):
        return 3


@location_bias_rule(sim.world, "book-worm")
def book_worm_rule(character: GameObject, location: GameObject) -> Optional[int]:
    if character.has_component(BookWorm) and location_has_activities(
        location, "Reading"
    ):
        return 2


@location_bias_rule(sim.world, "health-nut")
def rule(character: GameObject, location: GameObject) -> Optional[int]:
    if character.has_component(HealthNut) and location_has_activities(
        location, "Recreation"
    ):
        return 2


def main():
    ###############################
    # SPAWN NEW LOCATIONS
    ###############################

    register_activity_type(
        sim.world, GameObjectPrefab(name="Recreation", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world, GameObjectPrefab(name="Socializing", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world, GameObjectPrefab(name="Reading", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world, GameObjectPrefab(name="Shopping", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world,
        GameObjectPrefab(name="People Watching", components={"ActivityType": {}}),
    )
    register_activity_type(
        sim.world, GameObjectPrefab(name="Drinking", components={"ActivityType": {}})
    )

    # We need to step the simulation once to create all the activities
    sim.step()

    activity_library = sim.world.resource_manager.get_resource(ActivityLibrary)

    locations = [
        sim.world.gameobject_manager.spawn_gameobject(
            [
                Location(),
                Activities(
                    [
                        activity_library.get("Recreation"),
                        activity_library.get("Socializing"),
                    ]
                ),
            ],
            name="Gym",
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            [
                Location(),
                Activities(
                    [
                        activity_library.get("Reading"),
                    ]
                ),
            ],
            name="Library",
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            [
                Location(),
                Activities(
                    [
                        activity_library.get("Shopping"),
                        activity_library.get("Socializing"),
                        activity_library.get("People Watching"),
                    ]
                ),
            ],
            name="Mall",
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            [
                Location(),
                Activities(
                    [
                        activity_library.get("Drinking"),
                        activity_library.get("Socializing"),
                    ]
                ),
            ],
            name="Bar",
        ),
    ]

    characters = [
        sim.world.gameobject_manager.spawn_gameobject(
            [Actor("Alice"), HealthNut(), SocialButterfly()]
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            [Actor("James"), Shopaholic(), BookWorm(), HealthNut()]
        ),
        sim.world.gameobject_manager.spawn_gameobject(
            [Actor("Raven"), RecoveringAlcoholic(), HealthNut(), SocialButterfly()]
        ),
    ]

    for c in characters:
        # Score all the locations in the map
        probabilities = calculate_location_probabilities(c, locations)
        print(f"== {c.get_component(Actor).name} ==")
        print([(loc.name, prob) for prob, loc in probabilities])


if __name__ == "__main__":
    main()
