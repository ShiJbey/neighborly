import dataclasses
import random
from typing import List, Optional, Type, cast

from neighborly.components.character import (
    CharacterType,
    ChildOf,
    Family,
    GameCharacter,
    LifeStageType,
    Married,
    ParentOf,
    SiblingOf,
)
from neighborly.components.residence import (
    Residence,
    ResidenceType,
    Vacant,
    set_residence,
)
from neighborly.config import NeighborlyConfig
from neighborly.ecs import Active, GameObject, System, World
from neighborly.relationship import (
    Friendship,
    InteractionScore,
    Romance,
    add_relationship,
    get_relationship,
)
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.spawn_table import CharacterSpawnTable, ResidenceSpawnTable
from neighborly.time import SimDateTime
from neighborly.utils.common import get_random_child_character_type
from neighborly.world_map import BuildingMap

plugin_info = PluginInfo(
    name="default resident spawning plugin",
    plugin_id="default.resident_spawning",
    version="0.1.0",
)


@dataclasses.dataclass
class _GeneratedFamily:
    adults: List[GameObject] = dataclasses.field(default_factory=list)
    children: List[GameObject] = dataclasses.field(default_factory=list)


class SpawnFamilySystemBase(System):
    """Spawns new families in settlements.

    Note
    ----
    This system depends on the "new_families_per_year" setting in the simulation
    config. You can see how this setting is accessed in the run method below.
    """

    @staticmethod
    def _get_vacant_residences(world: World) -> List[GameObject]:
        """Get all active vacant residences."""
        return [
            world.gameobject_manager.get_gameobject(gid)
            for gid, _ in world.get_components((Residence, Active, Vacant))
        ]

    @staticmethod
    def _try_build_residence(world: World) -> Optional[GameObject]:
        building_map = world.resource_manager.get_resource(BuildingMap)
        vacancies = building_map.get_vacant_lots()
        spawn_table = world.resource_manager.get_resource(ResidenceSpawnTable)
        rng = world.resource_manager.get_resource(random.Random)

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return None

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(building_map.get_total_lots()) < 0.4:
            return None

        # Pick a random lot from those available
        lot_position = rng.choice(vacancies)

        residence_type = cast(
            Type[ResidenceType],
            world.resolve_component_type(spawn_table.choose_random(rng)),
        )

        residence = residence_type.instantiate(world, lot=lot_position)

        return residence

    @staticmethod
    def _spawn_family(world: World) -> _GeneratedFamily:
        spawn_table = world.resource_manager.get_resource(CharacterSpawnTable)
        rng = world.resource_manager.get_resource(random.Random)
        character_type = cast(
            Type[CharacterType],
            world.resolve_component_type(spawn_table.choose_random(rng)),
        )

        date = world.resource_manager.get_resource(SimDateTime)

        # Track all the characters generated
        generated_characters = _GeneratedFamily()

        # Create a new entity using the archetype
        character = character_type.instantiate(
            world, life_stage=LifeStageType.YoungAdult
        )

        generated_characters.adults.append(character)

        spouse: Optional[GameObject] = None

        if rng.random() < character_type.config.chance_spawn_with_spouse:
            spouse = character_type.instantiate(
                world,
                last_name=character.get_component(GameCharacter).last_name,
                life_stage=LifeStageType.Adult,
            )

            generated_characters.adults.append(spouse)

            # Configure relationship from character to spouse
            add_relationship(character, spouse)
            get_relationship(character, spouse).add_component(
                Married, timestamp=date.year
            )
            get_relationship(character, spouse).get_component(Romance).base_value += 45
            get_relationship(character, spouse).get_component(
                Friendship
            ).base_value += 30
            get_relationship(character, spouse).get_component(
                InteractionScore
            ).base_value += 1

            # Configure relationship from spouse to character
            add_relationship(spouse, character)
            get_relationship(spouse, character).add_component(
                Married, timestamp=date.year
            )
            get_relationship(spouse, character).get_component(Romance).base_value += 45
            get_relationship(spouse, character).get_component(
                Friendship
            ).base_value += 30
            get_relationship(spouse, character).get_component(
                InteractionScore
            ).base_value += 1

        num_kids: int = rng.randint(0, character_type.config.max_children_at_spawn)
        children: List[GameObject] = []

        for _ in range(num_kids):
            child_character_type = get_random_child_character_type(character, spouse)

            child = child_character_type.instantiate(
                world,
                last_name=character.get_component(GameCharacter).last_name,
                life_stage=LifeStageType.Child,
            )

            generated_characters.children.append(child)
            children.append(child)

            # Relationship of child to character
            add_relationship(child, character)
            get_relationship(child, character).add_component(
                ChildOf, timestamp=date.year
            )
            get_relationship(child, character).add_component(
                Family, timestamp=date.year
            )
            get_relationship(child, character).get_component(
                Friendship
            ).base_value += 20
            get_relationship(child, character).get_component(
                InteractionScore
            ).base_value += 1

            # Relationship of character to child
            add_relationship(character, child)
            get_relationship(character, child).add_component(
                ParentOf, timestamp=date.year
            )
            get_relationship(character, child).add_component(
                Family, timestamp=date.year
            )
            get_relationship(character, child).get_component(
                Friendship
            ).base_value += 20
            get_relationship(character, child).get_component(
                InteractionScore
            ).base_value += 1

            if spouse:
                # Relationship of child to spouse
                add_relationship(child, spouse)
                get_relationship(child, spouse).add_component(
                    ChildOf, timestamp=date.year
                )
                get_relationship(child, spouse).get_component(
                    Friendship
                ).base_value += 20
                get_relationship(child, spouse).get_component(
                    InteractionScore
                ).base_value += 1

                # Relationship of spouse to child
                add_relationship(spouse, child)
                get_relationship(spouse, child).add_component(
                    ParentOf, timestamp=date.year
                )

                get_relationship(spouse, child).add_component(
                    Family, timestamp=date.year
                )
                get_relationship(spouse, child).get_component(
                    Friendship
                ).base_value += 20

                get_relationship(spouse, child).get_component(
                    InteractionScore
                ).base_value += 1

            for sibling in children:
                # Relationship of child to sibling
                add_relationship(child, sibling)
                get_relationship(child, sibling).add_component(
                    SiblingOf, timestamp=date.year
                )

                get_relationship(child, sibling).add_component(
                    Family, timestamp=date.year
                )
                get_relationship(child, sibling).get_component(
                    Friendship
                ).base_value += 20
                get_relationship(child, sibling).get_component(
                    InteractionScore
                ).base_value += 1

                # Relationship of sibling to child
                add_relationship(sibling, child)
                get_relationship(sibling, child).add_component(
                    SiblingOf, timestamp=date.year
                )

                get_relationship(sibling, child).add_component(
                    Family, timestamp=date.year
                )
                get_relationship(sibling, child).get_component(
                    Friendship
                ).base_value += 20
                get_relationship(sibling, child).get_component(
                    InteractionScore
                ).base_value += 1

        return generated_characters

    def on_update(self, world: World) -> None:
        families_per_year: int = world.resource_manager.get_resource(
            NeighborlyConfig
        ).settings.get("new_families_per_year", 2)

        rng = world.resource_manager.get_resource(random.Random)

        for _ in range(families_per_year):
            # Try to find a vacant residence
            vacant_residences = self._get_vacant_residences(world)
            if vacant_residences:
                residence = rng.choice(vacant_residences)
            else:
                # Try to create a new house
                residence = self._try_build_residence(world)
                if residence is None:
                    break

            family = self._spawn_family(world)

            for adult in family.adults:
                set_residence(adult, residence, True)

            for child in family.children:
                set_residence(child, residence, False)


def setup(sim: Neighborly):
    sim.world.system_manager.add_system(SpawnFamilySystemBase())
