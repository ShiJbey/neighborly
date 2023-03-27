import dataclasses
import random
from typing import Any, List, Optional

from neighborly.components import (
    CharacterSpawnTable,
    ChildOf,
    CurrentSettlement,
    GameCharacter,
    MarriageConfig,
    ReproductionConfig,
    Residence,
    ResidenceSpawnTable,
    Vacant,
)
from neighborly.components.character import (
    Family,
    LifeStageType,
    Married,
    ParentOf,
    SiblingOf,
)
from neighborly.config import NeighborlyConfig
from neighborly.core.ecs import Active, GameObject
from neighborly.core.life_event import AllEvents
from neighborly.core.relationship import (
    Friendship,
    InteractionScore,
    Romance,
    add_relationship,
    add_relationship_status,
    get_relationship,
)
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.events import MoveResidenceEvent
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.systems import System
from neighborly.utils.common import (
    add_character_to_settlement,
    add_residence_to_settlement,
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


class SpawnFamilySystem(System):
    """Spawns new families in settlements

    This system runs every 6 months and spawns families into new or existing residences.

    Note
    ----
    This system depends on the "new_families_per_year" setting in the simulation
    config. You can see how this setting is accessed in the run method below.
    """

    sys_group = "early-update"

    def __init__(self) -> None:
        super().__init__(interval=TimeDelta(months=6))

    def _get_vacant_residences(self) -> List[GameObject]:
        return [
            self.world.get_gameobject(gid)
            for gid, _ in self.world.get_components(
                (Residence, Active, Vacant, CurrentSettlement)
            )
        ]

    def _try_build_residence(self, settlement: GameObject) -> Optional[GameObject]:
        land_map = settlement.get_component(Settlement).land_map
        vacancies = land_map.get_vacant_lots()
        spawn_table = settlement.get_component(ResidenceSpawnTable)
        rng = self.world.get_resource(random.Random)

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return None

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(land_map.get_total_lots()) < 0.4:
            return None

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        prefab = spawn_table.choose_random(rng)

        residence = spawn_residence(self.world, prefab)

        add_residence_to_settlement(
            residence,
            settlement=self.world.get_gameobject(settlement.uid),
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

    def _spawn_family(self, spawn_table: CharacterSpawnTable) -> _GeneratedFamily:
        rng = self.world.get_resource(random.Random)
        prefab = spawn_table.choose_random(rng)

        # Track all the characters generated
        generated_characters = _GeneratedFamily()

        # Create a new entity using the archetype
        character = spawn_character(
            self.world, prefab, life_stage=LifeStageType.YoungAdult
        )

        generated_characters.adults.append(character)

        spouse_prefab: Optional[str] = None
        spouse: Optional[GameObject] = None

        if marriage_config := character.try_component(MarriageConfig):
            spouse_prefab = self._try_get_spouse_prefab(
                rng, marriage_config, spawn_table
            )

        if spouse_prefab:
            spouse = spawn_character(
                self.world,
                spouse_prefab,
                last_name=character.get_component(GameCharacter).last_name,
                life_stage=LifeStageType.Adult,
            )

            generated_characters.adults.append(spouse)

            # Configure relationship from character to spouse
            add_relationship(character, spouse)
            add_relationship_status(character, spouse, Married())
            get_relationship(character, spouse).get_component(Romance).increment(45)
            get_relationship(character, spouse).get_component(Friendship).increment(30)
            get_relationship(character, spouse).get_component(
                InteractionScore
            ).increment(1)

            # Configure relationship from spouse to character
            add_relationship(spouse, character)
            add_relationship_status(spouse, character, Married())
            get_relationship(spouse, character).get_component(Romance).increment(45)
            get_relationship(spouse, character).get_component(Friendship).increment(30)
            get_relationship(spouse, character).get_component(
                InteractionScore
            ).increment(1)

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
                    self.world,
                    child_prefab,
                    last_name=character.get_component(GameCharacter).last_name,
                    life_stage=LifeStageType.Child,
                )
                generated_characters.children.append(child)
                children.append(child)

                # Relationship of child to character
                add_relationship(child, character)
                add_relationship_status(child, character, ChildOf())
                add_relationship_status(child, character, Family())
                get_relationship(child, character).get_component(Friendship).increment(
                    20
                )
                get_relationship(child, character).get_component(
                    InteractionScore
                ).increment(1)

                # Relationship of character to child
                add_relationship(character, child)
                add_relationship_status(character, child, ParentOf())
                add_relationship_status(character, child, Family())
                get_relationship(character, child).get_component(Friendship).increment(
                    20
                )
                get_relationship(character, child).get_component(
                    InteractionScore
                ).increment(1)

                if spouse:
                    # Relationship of child to spouse
                    add_relationship(child, spouse)
                    add_relationship_status(child, spouse, ChildOf())
                    get_relationship(child, spouse).get_component(Friendship).increment(
                        20
                    )
                    get_relationship(child, spouse).get_component(
                        InteractionScore
                    ).increment(1)

                    # Relationship of spouse to child
                    add_relationship(spouse, child)
                    add_relationship_status(spouse, child, ParentOf())
                    add_relationship_status(spouse, child, Family())
                    get_relationship(spouse, child).get_component(Friendship).increment(
                        20
                    )
                    get_relationship(spouse, child).get_component(
                        InteractionScore
                    ).increment(1)

                for sibling in children:
                    # Relationship of child to sibling
                    add_relationship(child, sibling)
                    add_relationship_status(child, sibling, SiblingOf())
                    add_relationship_status(child, sibling, Family())
                    get_relationship(child, sibling).get_component(
                        Friendship
                    ).increment(20)
                    get_relationship(child, sibling).get_component(
                        InteractionScore
                    ).increment(1)

                    # Relationship of sibling to child
                    add_relationship(sibling, child)
                    add_relationship_status(sibling, child, SiblingOf())
                    add_relationship_status(sibling, child, Family())
                    get_relationship(sibling, child).get_component(
                        Friendship
                    ).increment(20)
                    get_relationship(sibling, child).get_component(
                        InteractionScore
                    ).increment(1)

        return generated_characters

    def run(self, *args: Any, **kwargs: Any) -> None:
        families_per_year: int = self.world.get_resource(NeighborlyConfig).settings.get(
            "new_families_per_year", 10
        )
        families_to_spawn = families_per_year // 2

        rng = self.world.get_resource(random.Random)
        all_events = self.world.get_resource(AllEvents)
        date = self.world.get_resource(SimDateTime)

        # Spawn families in each settlement
        for guid, (settlement, character_spawn_table) in self.world.get_components(
            (Settlement, CharacterSpawnTable)
        ):
            settlement_entity = self.world.get_gameobject(guid)

            for _ in range(families_to_spawn):
                # Try to find a vacant residence
                vacant_residences = self._get_vacant_residences()
                if vacant_residences:
                    residence = rng.choice(vacant_residences)
                else:
                    # Try to create a new house
                    residence = self._try_build_residence(settlement_entity)
                    if residence is None:
                        break

                family = self._spawn_family(character_spawn_table)

                event = MoveResidenceEvent(
                    date, residence, *[*family.adults, *family.children]
                )

                for adult in family.adults:
                    add_character_to_settlement(adult, settlement.gameobject)
                    set_residence(adult, residence, True)
                    adult.fire_event(event)

                for child in family.children:
                    add_character_to_settlement(child, settlement.gameobject)
                    set_residence(child, residence, False)
                    child.fire_event(event)

                # Record a life event
                all_events.append(event)


def setup(sim: Neighborly, **kwargs: Any):
    sim.add_system(SpawnFamilySystem())
