#!/usr/bin/env python3
"""
Using Authored Characters Sample
--------------------------------

This samples shows how users may inject user-specified characters into the simulation.
Normally characters are spawned into the settlement based on the spawn table.
"""
import time
from typing import Any, Dict

from neighborly import Neighborly, NeighborlyConfig, SimDateTime, SystemBase
from neighborly.components.character import GameCharacter
from neighborly.core.ecs import GameObjectPrefab, TagComponent, World
from neighborly.core.relationship import (
    Friendship,
    InteractionScore,
    RelationshipManager,
    Romance,
)
from neighborly.core.settlement import Settlement
from neighborly.core.status import IStatus, Statuses
from neighborly.data_collection import DataCollector
from neighborly.decorators import component, system
from neighborly.exporter import export_to_json
from neighborly.utils.common import (
    add_residence_to_settlement,
    set_character_settlement,
    set_residence,
    spawn_character,
    spawn_residence,
)

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            "relationship_schema": {
                "components": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                }
            },
            "plugins": [
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown",
            ],
            "settings": {
                "settlement_name": "Westworld",
                "settlement_size": (5, 5),  # Width/length of the settlement grid
                "zoning": (0.5, 0.5),  # Zoning is 50/50 residential vs. commercial
                "character_spawn_table": [
                    {"name": "character::default::male"},
                    {"name": "character::default::female"},
                    {"name": "character::default::non-binary"},
                ],
                "residence_spawn_table": [
                    {"name": "residence::default::house"},
                ],
                "business_spawn_table": [],
            },
        }
    )
)


@component(sim.world)
class Robot(TagComponent):
    """Tags a character as a Robot"""

    pass


@component(sim.world)
class OwesDebt(IStatus):
    """Marks a character as owing money to another character"""

    def __init__(self, year_created: int, amount: int) -> None:
        super().__init__(year_created)
        self.amount: int = amount

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "amount": self.amount}


@system(sim.world)
class RelationshipReporter(SystemBase):
    def on_create(self, world: World) -> None:
        world.resource_manager.get_resource(DataCollector).create_new_table(
            "relationships",
            (
                "timestamp",
                "owner",
                "target",
                "friendship",
                "romance",
                "interaction_score",
                "statuses",
            ),
        )

    def on_update(self, world: World) -> None:
        timestamp = world.resource_manager.get_resource(SimDateTime).to_iso_str()
        data_collector = world.resource_manager.get_resource(DataCollector)
        for guid, (game_character, relationship_manager) in world.get_components(
            (GameCharacter, RelationshipManager)
        ):
            if (
                game_character.first_name == "Delores"
                and game_character.last_name == "Abernathy"
            ):
                for target, relationship in relationship_manager.outgoing.items():
                    data_collector.add_table_row(
                        "relationships",
                        {
                            "timestamp": timestamp,
                            "owner": guid,
                            "target": target.uid,
                            "friendship": relationship.get_component(
                                Friendship
                            ).value,
                            "romance": relationship.get_component(Romance).value,
                            "interaction_score": relationship.get_component(
                                InteractionScore
                            ).value,
                            "statuses": str(relationship.get_component(Statuses)),
                        },
                    )


EXPORT_SIM = False
YEARS_TO_SIMULATE = 50


def main():
    """Main entry point for this module"""
    sim.world.gameobject_manager.add_prefab(
        GameObjectPrefab(
            name="westworld::host",
            extends=["character::default::female"],
            components={"Robot": {}},
        )
    )

    sim.step()

    west_world = sim.world.gameobject_manager.get_gameobject(
        sim.world.get_component(Settlement)[0][0]
    )

    dolores = spawn_character(
        sim.world,
        "westworld::host",
        first_name="Dolores",
        last_name="Abernathy",
        age=32,
    )

    set_character_settlement(dolores, west_world)

    house = spawn_residence(sim.world, "residence::default::house")

    add_residence_to_settlement(house, west_world)

    set_residence(dolores, house)

    st = time.time()
    sim.run_for(YEARS_TO_SIMULATE)
    elapsed_time = time.time() - st

    print(f"World Date: {str(sim.world.resource_manager.get_resource(SimDateTime))}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_SIM:
        with open(f"neighborly_{sim.config.seed}.json", "w") as f:
            f.write(export_to_json(sim))


if __name__ == "__main__":
    main()
