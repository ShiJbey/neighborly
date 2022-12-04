from __future__ import annotations

from random import Random
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from neighborly.builtin.ai import DefaultMovementModule
from neighborly.builtin.components import Active, Age, CanAge, CanGetPregnant, Lifespan
from neighborly.core.ai import MovementAI
from neighborly.core.archetypes import (
    IBusinessArchetype,
    ICharacterArchetype,
    IResidenceArchetype,
    ResidentialZoning,
)
from neighborly.core.business import (
    Business,
    IBusinessType,
    InTheWorkforce,
    Services,
    ServiceType,
    ServiceTypes,
    Unemployed,
    WorkHistory,
    parse_operating_hour_str,
)
from neighborly.core.character import (
    CharacterAgingConfig,
    GameCharacter,
    Gender,
    GenderValue,
    LifeStage,
    LifeStageValue,
)
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationships
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine
from neighborly.core.status import add_status


class BaseCharacterArchetype(ICharacterArchetype):
    """Base factory class for constructing new characters"""

    __slots__ = (
        "spawn_frequency",
        "chance_spawn_with_spouse",
        "max_children_at_spawn",
    )

    def __init__(
        self,
        spawn_frequency: int = 1,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 0,
    ) -> None:
        self.spawn_frequency: int = spawn_frequency
        self.max_children_at_spawn: int = max_children_at_spawn
        self.chance_spawn_with_spouse: float = chance_spawn_with_spouse

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_spawn_frequency(self) -> int:
        return self.spawn_frequency

    def get_max_children_at_spawn(self) -> int:
        """Return the maximum amount of children this prefab can have when spawning"""
        return self.max_children_at_spawn

    def get_chance_spawn_with_spouse(self) -> float:
        """Return the chance that a character from this prefab spawns with a spouse"""
        return self.chance_spawn_with_spouse

    def create(self, world: World, **kwargs: Any) -> GameObject:
        # Perform calculations first and return the base character GameObject
        return world.spawn_gameobject(
            [
                Active(),
                GameCharacter("First", "Last"),
                Routine(),
                Age(),
                WorkHistory(),
                CharacterAgingConfig(
                    lifespan=83,
                    child_age=0,
                    adolescent_age=13,
                    young_adult_age=18,
                    adult_age=30,
                    senior_age=65,
                ),
                PersonalValues.create(world),
                Relationships(),
                MovementAI(DefaultMovementModule()),
            ]
        )


class HumanArchetype(BaseCharacterArchetype):
    def __init__(
        self,
        spawn_frequency: int = 1,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 0,
    ) -> None:
        super().__init__(
            spawn_frequency=spawn_frequency,
            chance_spawn_with_spouse=chance_spawn_with_spouse,
            max_children_at_spawn=max_children_at_spawn,
        )

    def create(self, world: World, **kwargs: Any) -> GameObject:
        # Perform calculations first and return the base character GameObject
        gameobject = super().create(world, **kwargs)

        engine = world.get_resource(NeighborlyEngine)

        life_stage: str = kwargs.get("life_stage", "young_adult")
        age: Optional[int] = kwargs.get("age")

        gameobject.add_component(CanAge())
        gameobject.add_component(
            CharacterAgingConfig(
                lifespan=83,
                child_age=0,
                adolescent_age=13,
                young_adult_age=18,
                adult_age=30,
                senior_age=65,
            )
        )

        if age is not None:
            # Age takes priority over life stage if both are given
            gameobject.add_component(Age(age))
            gameobject.add_component(
                LifeStage(
                    self._life_stage_from_age(
                        gameobject.get_component(CharacterAgingConfig), age
                    )
                )
            )
        else:
            gameobject.add_component(LifeStage(self._life_stage_from_str(life_stage)))
            gameobject.add_component(
                Age(
                    self._generate_age_from_life_stage(
                        engine.rng,
                        gameobject.get_component(CharacterAgingConfig),
                        life_stage,
                    )
                )
            )

        # gender
        gender: GenderValue = engine.rng.choice(list(GenderValue))
        gameobject.add_component(Gender(gender))

        # Initialize employment status
        if life_stage == "young_adult" or life_stage == "adult":
            gameobject.add_component(InTheWorkforce())
            add_status(world, gameobject, Unemployed(30))

        if self._fertility_from_gender(world, gender):
            gameobject.add_component(CanGetPregnant())

        # name
        first_name, last_name = self._generate_name_from_gender(world, gender)
        character_component = gameobject.get_component(GameCharacter)
        character_component.first_name = first_name
        character_component.last_name = last_name

        return gameobject

    def _life_stage_from_age(
        self, aging_config: CharacterAgingConfig, age: int
    ) -> LifeStageValue:
        """Determine the life stage of a character given an age"""
        if 0 <= age < aging_config.adolescent_age:
            return LifeStageValue.Child
        elif aging_config.adolescent_age <= age < aging_config.young_adult_age:
            return LifeStageValue.Adolescent
        elif aging_config.young_adult_age <= age < aging_config.adult_age:
            return LifeStageValue.YoungAdult
        elif aging_config.adult_age <= age < aging_config.senior_age:
            return LifeStageValue.Adult
        else:
            return LifeStageValue.Senior

    def _generate_age_from_life_stage(
        self, rng: Random, aging_config: CharacterAgingConfig, life_stage: str
    ) -> int:
        """Generates a random age given a life stage"""

        if life_stage == "child":
            return rng.randint(0, aging_config.adolescent_age - 1)
        elif life_stage == "teen":
            return rng.randint(
                aging_config.adolescent_age,
                aging_config.young_adult_age - 1,
            )
        elif life_stage == "young_adult":
            return rng.randint(
                aging_config.young_adult_age,
                aging_config.adult_age - 1,
            )
        elif life_stage == "adult":
            return rng.randint(
                aging_config.adult_age,
                aging_config.senior_age - 1,
            )
        else:
            return aging_config.senior_age + int(10 * rng.random())

    def _life_stage_from_str(self, life_stage: str) -> LifeStageValue:
        """Return the proper component given the life stage"""
        stages = {
            "child": LifeStageValue.Child,
            "adolescent": LifeStageValue.Adolescent,
            "young_adult": LifeStageValue.YoungAdult,
            "adult": LifeStageValue.Adult,
            "senior": LifeStageValue.Senior,
        }
        return stages[life_stage]

    def _fertility_from_gender(self, world: World, gender: GenderValue) -> bool:
        """Return true if this character can get pregnant given their gender"""
        engine = world.get_resource(NeighborlyEngine)

        if gender == GenderValue.Female:
            return engine.rng.random() < 0.8
        elif gender == GenderValue.Male:
            return False
        else:
            return engine.rng.random() < 0.5

    def _generate_name_from_gender(
        self, world: World, gender: GenderValue
    ) -> Tuple[str, str]:
        """Generate a name for the character given their gender"""
        engine = world.get_resource(NeighborlyEngine)

        if gender == GenderValue.Male:
            first_name_category = "#masculine_first_name#"
        elif gender == GenderValue.Female:
            first_name_category = "#feminine_first_name#"
        else:
            first_name_category = "#first_name#"

        first_name = engine.name_generator.get_name(first_name_category)
        last_name = engine.name_generator.get_name("#family_name#")

        return first_name, last_name


class BaseBusinessArchetype(IBusinessArchetype):
    """
    Shared information about all businesses that
    have this type
    """

    __slots__ = (
        "business_type",
        "hours",
        "name_format",
        "owner_type",
        "max_instances",
        "min_population",
        "employee_types",
        "services",
        "spawn_frequency",
        "year_available",
        "year_obsolete",
        "instances",
    )

    def __init__(
        self,
        business_type: Type[IBusinessType],
        name_format: str,
        hours: str = "day",
        owner_type: Optional[str] = None,
        max_instances: int = 9999,
        min_population: int = 0,
        employee_types: Optional[Dict[str, int]] = None,
        services: Optional[List[str]] = None,
        spawn_frequency: int = 1,
        year_available: int = -1,
        year_obsolete: int = 9999,
        average_lifespan: int = 20,
    ) -> None:
        self.business_type: Type[IBusinessType] = business_type
        self.hours: str = hours
        self.name_format: str = name_format
        self.owner_type: Optional[str] = owner_type
        self.max_instances: int = max_instances
        self.min_population: int = min_population
        self.employee_types: Dict[str, int] = employee_types if employee_types else {}
        self.services: List[str] = services if services else []
        self.spawn_frequency: int = spawn_frequency
        self.year_available: int = year_available
        self.year_obsolete: int = year_obsolete
        self.instances: int = 0
        self.average_lifespan: int = average_lifespan

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
        return self.spawn_frequency

    def get_min_population(self) -> int:
        """Return the minimum population needed for this business to be constructed"""
        return self.min_population

    def get_year_available(self) -> int:
        """Return the year that this business is available to construct"""
        return self.year_available

    def get_year_obsolete(self) -> int:
        """Return the year that this business is no longer available to construct"""
        return self.year_obsolete

    def get_business_type(self) -> Type[IBusinessType]:
        return self.business_type

    def get_instances(self) -> int:
        return self.instances

    def set_instances(self, value: int) -> None:
        self.instances = value

    def get_max_instances(self) -> int:
        return self.max_instances

    def create(self, world: World, **kwargs: Any) -> GameObject:
        engine = world.get_resource(NeighborlyEngine)

        services: Set[ServiceType] = set()

        for service in self.services:
            services.add(ServiceTypes.get(service))

        return world.spawn_gameobject(
            [
                self.business_type(),
                Business(
                    name=engine.name_generator.get_name(self.name_format),
                    operating_hours=parse_operating_hour_str(self.hours),
                    owner_type=self.owner_type,
                    open_positions=self.employee_types,
                ),
                Age(0),
                Services(services),
                Position2D(),
                Location(),
                Lifespan(self.average_lifespan),
            ]
        )


class BaseResidenceArchetype(IResidenceArchetype):
    __slots__ = ("spawn_frequency", "zoning")

    def __init__(
        self,
        zoning: ResidentialZoning = ResidentialZoning.SingleFamily,
        spawn_frequency: int = 1,
    ) -> None:
        self.spawn_frequency: int = spawn_frequency
        self.zoning: ResidentialZoning = zoning

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_spawn_frequency(self) -> int:
        return self.spawn_frequency

    def get_zoning(self) -> ResidentialZoning:
        return self.zoning

    def create(self, world: World, **kwargs: Any) -> GameObject:
        return world.spawn_gameobject([Residence(), Location(), Position2D()])
