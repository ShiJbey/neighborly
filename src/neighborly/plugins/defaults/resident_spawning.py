import dataclasses
import random
from typing import List, Optional

from neighborly.components.character import (
    ChildOf,
    Family,
    GameCharacter,
    LifeStageType,
    MarriageConfig,
    Married,
    ParentOf,
    ReproductionConfig,
    SiblingOf,
)
from neighborly.components.residence import Residence, Vacant
from neighborly.components.shared import CurrentSettlement
from neighborly.components.spawn_table import CharacterSpawnTable, ResidenceSpawnTable
from neighborly.config import NeighborlyConfig
from neighborly.core.ecs import Active, GameObject, SystemBase, World
from neighborly.core.relationship import (
    Friendship,
    InteractionScore,
    Romance,
    add_relationship,
    add_relationship_status,
    get_relationship,
)
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime
from neighborly.events import MoveResidenceEvent
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.common import (
    add_residence_to_settlement,
    set_character_settlement,
    set_residence,
    spawn_character,
    spawn_residence,
)

plugin_info = PluginInfo(
    name="default resident spawning plugin",
    plugin_id="default.resident_spawning",
    version="0.1.0",
)


@dataclasses.dataclass
class _GeneratedFamily:
    adults: List[GameObject] = dataclasses.field(default_factory=list)
    children: List[GameObject] = dataclasses.field(default_factory=list)


class SpawnFamilySystemBase(SystemBase):
    """Spawns new families in settlements.

    Note
    ----
    This system depends on the "new_families_per_year" setting in the simulation
    config. You can see how this setting is accessed in the run method below.
    """

    @staticmethod
    def _get_vacant_residences(world: World) -> List[GameObject]:
        return [
            world.gameobject_manager.get_gameobject(gid)
            for gid, _ in world.get_components(
                (Residence, Active, Vacant, CurrentSettlement)
            )
        ]

    @staticmethod
    def _try_build_residence(
        world: World, settlement: GameObject
    ) -> Optional[GameObject]:
        land_map = settlement.get_component(Settlement).land_map
        vacancies = land_map.get_vacant_lots()
        spawn_table = settlement.get_component(ResidenceSpawnTable)
        rng = world.resource_manager.get_resource(random.Random)

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return None

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(land_map.get_total_lots()) < 0.4:
            return None

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        prefab = spawn_table.choose_random(rng)

        residence = spawn_residence(world, prefab)

        add_residence_to_settlement(
            residence,
            settlement=settlement,
            lot_id=lot,
        )

        return residence

    @staticmethod
    def _try_get_spouse_prefab(
        rng: random.Random,
        marriage_config: MarriageConfig,
        spawn_table: CharacterSpawnTable,
    ) -> Optional[str]:
        if rng.random() < marriage_config.chance_spawn_with_spouse:
            # Create another character to be their spouse
            potential_spouse_prefabs = spawn_table.get_matching_prefabs(
                *marriage_config.spouse_prefabs
            )

            if potential_spouse_prefabs:
                return rng.choice(potential_spouse_prefabs)

        return None

    @staticmethod
    def _spawn_family(
        world: World, spawn_table: CharacterSpawnTable
    ) -> _GeneratedFamily:
        rng = world.resource_manager.get_resource(random.Random)
        prefab = spawn_table.choose_random(rng)
        date = world.resource_manager.get_resource(SimDateTime)

        # Track all the characters generated
        generated_characters = _GeneratedFamily()

        # Create a new entity using the archetype
        character = spawn_character(world, prefab, life_stage=LifeStageType.YoungAdult)

        generated_characters.adults.append(character)

        spouse_prefab: Optional[str] = None
        spouse: Optional[GameObject] = None

        if marriage_config := character.try_component(MarriageConfig):
            spouse_prefab = SpawnFamilySystemBase._try_get_spouse_prefab(
                rng, marriage_config, spawn_table
            )

        if spouse_prefab:
            spouse = spawn_character(
                world=world,
                prefab=spouse_prefab,
                last_name=character.get_component(GameCharacter).last_name,
                life_stage=LifeStageType.Adult,
            )

            generated_characters.adults.append(spouse)

            # Configure relationship from character to spouse
            add_relationship(character, spouse)
            add_relationship_status(character, spouse, Married(year_created=date.year))
            get_relationship(character, spouse).get_component(Romance).base_value += 45
            get_relationship(character, spouse).get_component(Friendship).base_value += 30
            get_relationship(character, spouse).get_component(
                InteractionScore
            ).base_value += 1

            # Configure relationship from spouse to character
            add_relationship(spouse, character)
            add_relationship_status(spouse, character, Married(year_created=date.year))
            get_relationship(spouse, character).get_component(Romance).base_value += 45
            get_relationship(spouse, character).get_component(Friendship).base_value += 30
            get_relationship(spouse, character).get_component(
                InteractionScore
            ).base_value += 1

        num_kids: int = 0
        children: List[GameObject] = []
        potential_child_prefabs: List[str] = []

        if reproduction_config := character.get_component(ReproductionConfig):
            num_kids = rng.randint(0, reproduction_config.max_children_at_spawn)

            potential_child_prefabs = spawn_table.get_matching_prefabs(
                *reproduction_config.child_prefabs
            )

        if potential_child_prefabs:
            chosen_child_prefabs = rng.sample(potential_child_prefabs, num_kids)

            for child_prefab in chosen_child_prefabs:
                child = spawn_character(
                    world,
                    child_prefab,
                    last_name=character.get_component(GameCharacter).last_name,
                    life_stage=LifeStageType.Child,
                )

                generated_characters.children.append(child)
                children.append(child)

                # Relationship of child to character
                add_relationship(child, character)
                add_relationship_status(
                    child, character, ChildOf(year_created=date.year)
                )
                add_relationship_status(
                    child, character, Family(year_created=date.year)
                )
                get_relationship(child, character).get_component(Friendship).base_value += 20
                get_relationship(child, character).get_component(InteractionScore).base_value += 1

                # Relationship of character to child
                add_relationship(character, child)
                add_relationship_status(
                    character, child, ParentOf(year_created=date.year)
                )
                add_relationship_status(
                    character, child, Family(year_created=date.year)
                )
                get_relationship(character, child).get_component(Friendship).base_value += 20
                get_relationship(character, child).get_component(
                    InteractionScore
                ).base_value += 1

                if spouse:
                    # Relationship of child to spouse
                    add_relationship(child, spouse)
                    add_relationship_status(
                        child, spouse, ChildOf(year_created=date.year)
                    )
                    get_relationship(child, spouse).get_component(Friendship).base_value += 20
                    get_relationship(child, spouse).get_component(
                        InteractionScore
                    ).base_value += 1

                    # Relationship of spouse to child
                    add_relationship(spouse, child)
                    add_relationship_status(
                        spouse, child, ParentOf(year_created=date.year)
                    )
                    add_relationship_status(
                        spouse, child, Family(year_created=date.year)
                    )
                    get_relationship(spouse, child).get_component(Friendship).base_value += 20

                    get_relationship(spouse, child).get_component(
                        InteractionScore
                    ).base_value += 1

                for sibling in children:
                    # Relationship of child to sibling
                    add_relationship(child, sibling)
                    add_relationship_status(
                        child, sibling, SiblingOf(year_created=date.year)
                    )
                    add_relationship_status(
                        child, sibling, Family(year_created=date.year)
                    )
                    get_relationship(child, sibling).get_component(
                        Friendship
                    ).base_value += 20
                    get_relationship(child, sibling).get_component(
                        InteractionScore
                    ).base_value += 1

                    # Relationship of sibling to child
                    add_relationship(sibling, child)
                    add_relationship_status(
                        sibling, child, SiblingOf(year_created=date.year)
                    )
                    add_relationship_status(
                        sibling, child, Family(year_created=date.year)
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
        date = world.resource_manager.get_resource(SimDateTime)

        # Spawn families in each settlement
        for guid, (settlement, character_spawn_table) in world.get_components(
            (Settlement, CharacterSpawnTable)
        ):
            settlement_entity = world.gameobject_manager.get_gameobject(guid)

            for _ in range(families_per_year):
                # Try to find a vacant residence
                vacant_residences = self._get_vacant_residences(world)
                if vacant_residences:
                    residence = rng.choice(vacant_residences)
                else:
                    # Try to create a new house
                    residence = self._try_build_residence(world, settlement_entity)
                    if residence is None:
                        break

                family = self._spawn_family(world, character_spawn_table)

                event = MoveResidenceEvent(
                    world, date, residence, *[*family.adults, *family.children]
                )

                for adult in family.adults:
                    set_character_settlement(adult, settlement_entity)
                    set_residence(adult, residence, True)

                for child in family.children:
                    set_character_settlement(child, settlement_entity)
                    set_residence(child, residence, False)

                event.dispatch()


def setup(sim: Neighborly):
    sim.world.system_manager.add_system(SpawnFamilySystemBase())
