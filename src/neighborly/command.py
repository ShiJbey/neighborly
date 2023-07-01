"""neighborly.command

Neighborly uses a command pattern to help with tracking simulation modifications.

"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional

from neighborly.components.character import (
    AgingConfig,
    GameCharacter,
    Gender,
    GenderType,
    LifeStage,
    LifeStageType,
)
from neighborly.components.shared import Age, Name, PrefabName
from neighborly.core.ecs import GameObject, World
from neighborly.core.time import SimDateTime
from neighborly.events import (
    CharacterAgeChangeEvent,
    CharacterCreatedEvent,
    CharacterNameChangeEvent,
    NewBusinessEvent,
    ResidenceCreatedEvent,
    SettlementCreatedEvent,
)


class SimCommand(ABC):
    """Simulation commands modify the state of the simulation."""

    @abstractmethod
    def execute(self, world: World) -> SimCommand:
        raise NotImplementedError()


class SpawnCharacter(SimCommand):
    """Spawn a new character into the world"""

    def __init__(
        self,
        prefab: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age: Optional[int] = None,
        life_stage: Optional[LifeStageType] = None,
        gender: Optional[GenderType] = None,
    ) -> None:
        super().__init__()
        self.prefab = prefab
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.life_stage = life_stage
        self.gender = gender
        self.result = None

    def execute(self, world: World) -> SpawnCharacter:
        character = world.gameobject_manager.instantiate_prefab(self.prefab)

        SetCharacterAge(
            character,
            self._generate_age_from_life_stage(
                world.resource_manager.get_resource(random.Random),
                character.get_component(AgingConfig),
                LifeStageType.YoungAdult,
            ),
        ).execute(world)

        if self.first_name:
            SetCharacterName(character, first_name=self.first_name).execute(world)

        if self.last_name:
            SetCharacterName(character, last_name=self.last_name).execute(world)

        if self.age is not None or self.life_stage is not None:
            SetCharacterAge(
                character, new_age=self.age, new_life_stage=self.life_stage
            ).execute(world)

        if self.gender:
            character.get_component(Gender).gender = self.gender

        character.name = (
            f"{character.get_component(GameCharacter).full_name}({character.uid})"
        )

        character.add_component(PrefabName(self.prefab))

        new_character_event = CharacterCreatedEvent(
            world=world,
            date=world.resource_manager.get_resource(SimDateTime),
            character=character,
        )

        self.result = character

        world.event_manager.dispatch_event(new_character_event)

        return self

    def get_result(self) -> GameObject:
        if self.result is not None:
            return self.result
        raise RuntimeError(f"{type(self)} Command failed.")

    @staticmethod
    def _generate_age_from_life_stage(
        rng: random.Random, aging_config: AgingConfig, life_stage_type: LifeStageType
    ) -> int:
        """Return an age for the character given their life_stage"""
        if life_stage_type == LifeStageType.Child:
            return rng.randint(0, aging_config.adolescent_age - 1)
        elif life_stage_type == LifeStageType.Adolescent:
            return rng.randint(
                aging_config.adolescent_age,
                aging_config.young_adult_age - 1,
            )
        elif life_stage_type == LifeStageType.YoungAdult:
            return rng.randint(
                aging_config.young_adult_age,
                aging_config.adult_age - 1,
            )
        elif life_stage_type == LifeStageType.Adult:
            return rng.randint(
                aging_config.adult_age,
                aging_config.senior_age - 1,
            )
        else:
            return aging_config.senior_age + int(10 * rng.random())


class SetCharacterAge(SimCommand):
    def __init__(
        self,
        character: GameObject,
        new_age: Optional[float] = None,
        new_life_stage: Optional[LifeStageType] = None,
    ) -> None:
        super().__init__()
        self.character = character
        self.new_age = new_age
        self.new_life_stage = new_life_stage

    def execute(self, world: World) -> SetCharacterAge:
        """Sets the name of a business"""
        if self.new_age is not None:
            SetCharacterAge._set_age(self.character, self.new_age)
        elif self.new_life_stage is not None:
            SetCharacterAge._set_life_stage(self.character, self.new_life_stage)
        else:
            raise ValueError("new_age or new_life_stage must be set")

        world.event_manager.dispatch_event(
            CharacterAgeChangeEvent(
                world,
                world.resource_manager.get_resource(SimDateTime).copy(),
                self.character,
                self.character.get_component(Age).value,
                self.character.get_component(LifeStage).life_stage,
            )
        )

        return self

    @staticmethod
    def _set_age(character: GameObject, new_age: float) -> None:
        age = character.get_component(Age)
        age.value = new_age

        if not character.has_component(AgingConfig):
            raise Exception(
                "Cannot set life stage for a character without an AgingConfig component"
            )

        aging_config = character.get_component(AgingConfig)

        life_stage = character.get_component(LifeStage)

        if age.value >= aging_config.senior_age:
            life_stage.life_stage = LifeStageType.Senior

        elif age.value >= aging_config.adult_age:
            life_stage.life_stage = LifeStageType.Adult

        elif age.value >= aging_config.young_adult_age:
            life_stage.life_stage = LifeStageType.YoungAdult

        elif age.value >= aging_config.adolescent_age:
            life_stage.life_stage = LifeStageType.Adolescent

        else:
            life_stage.life_stage = LifeStageType.Child

    @staticmethod
    def _set_life_stage(character: GameObject, life_stage_type: LifeStageType) -> None:
        """Sets the name of a business"""
        age = character.get_component(Age)

        if not character.has_component(AgingConfig):
            raise Exception(
                "Cannot set life stage for a character without an AgingConfig component"
            )

        aging_config = character.get_component(AgingConfig)

        character.get_component(LifeStage).life_stage = life_stage_type

        if life_stage_type == LifeStageType.Senior:
            age.value = aging_config.senior_age

        elif life_stage_type == LifeStageType.Adult:
            age.value = aging_config.adult_age

        elif life_stage_type == LifeStageType.YoungAdult:
            age.value = aging_config.young_adult_age

        elif life_stage_type == LifeStageType.Adolescent:
            age.value = aging_config.adolescent_age

        elif life_stage_type == LifeStageType.Child:
            age.value = 0


class SetCharacterName(SimCommand):
    def __init__(
        self, character: GameObject, first_name: str = "", last_name: str = ""
    ) -> None:
        super().__init__()
        self.character = character
        self.first_name = first_name
        self.last_name = last_name

    def execute(self, world: World) -> SetCharacterName:
        """Sets the name of a business"""
        game_character = self.character.get_component(GameCharacter)

        if self.first_name:
            game_character.first_name = self.first_name

        if self.last_name:
            game_character.last_name = self.last_name

        # self.character.get_component(Name).value = game_character.full_name

        self.character.name = f"{game_character.full_name}({self.character.uid})"

        world.event_manager.dispatch_event(
            CharacterNameChangeEvent(
                world,
                world.resource_manager.get_resource(SimDateTime).copy(),
                self.character,
                game_character.first_name,
                game_character.last_name,
            )
        )

        return self


class SpawnSettlement(SimCommand):
    def __init__(self, prefab: str = "settlement", name: str = "") -> None:
        super().__init__()
        self.prefab = prefab
        self.name = name
        self.result = None

    def execute(self, world: World) -> SpawnSettlement:
        """Create a new Settlement GameObject and add it to the world

        Parameters
        ----------
        world
            The world instance to add the settlement to

        Returns
        -------
        GameObject
            The newly created Settlement GameObject
        """
        settlement = world.gameobject_manager.instantiate_prefab(self.prefab)

        if self.name:
            settlement.get_component(Name).value = self.name

        settlement.name = settlement.get_component(Name).value

        new_settlement_event = SettlementCreatedEvent(
            world=world,
            date=world.resource_manager.get_resource(SimDateTime),
            settlement=settlement,
        )

        world.event_manager.dispatch_event(new_settlement_event)

        self.result = settlement

        return self

    def get_result(self) -> GameObject:
        if self.result is not None:
            return self.result
        raise RuntimeError(f"{type(self)} Command failed.")


class SpawnResidence(SimCommand):
    """Spawn a new residential building."""

    __slots__ = "prefab", "result"

    prefab: str
    """The name of a prefab to instantiate."""

    result: Optional[GameObject]
    """The residence GameObject."""

    def __init__(self, prefab: str) -> None:
        super().__init__()
        self.prefab = prefab
        self.result = None

    def execute(
        self,
        world: World,
    ) -> SpawnResidence:
        residence = world.gameobject_manager.instantiate_prefab(self.prefab)

        world.event_manager.dispatch_event(
            ResidenceCreatedEvent(
                world=world,
                timestamp=world.resource_manager.get_resource(SimDateTime),
                residence=residence,
            )
        )

        residence.add_component(PrefabName(self.prefab))

        residence.name = f"{self.prefab}({residence.uid})"

        self.result = residence

        return self

    def get_result(self) -> GameObject:
        if self.result is not None:
            return self.result
        raise RuntimeError(f"{type(self)} Command failed.")


class SpawnBusiness(SimCommand):
    """Spawn a new business."""

    __slots__ = "prefab", "result", "name"

    prefab: str
    """The name of a prefab to instantiate."""

    result: Optional[GameObject]
    """The residence GameObject."""

    name: str
    """The name of the business"""

    def __init__(self, prefab: str, name: str = "") -> None:
        super().__init__()
        self.prefab = prefab
        self.result = None
        self.name = name

    def execute(
        self,
        world: World,
    ) -> SpawnBusiness:
        business = world.gameobject_manager.instantiate_prefab(self.prefab)

        if self.name:
            business.get_component(Name).value = self.name

        business.name = f"{business.get_component(Name).value}({business.uid})"

        business.add_component(PrefabName(self.prefab))

        new_business_event = NewBusinessEvent(
            world=world,
            date=world.resource_manager.get_resource(SimDateTime),
            business=business,
        )

        business.world.event_manager.dispatch_event(new_business_event)

        self.result = business

        return self

    def get_result(self) -> GameObject:
        if self.result is not None:
            return self.result
        raise RuntimeError(f"{type(self)} Command failed.")
