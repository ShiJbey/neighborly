from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from neighborly.components.business import (
    Business,
    IBusinessType,
    InTheWorkforce,
    Services,
    ServiceType,
    ServiceTypes,
    WorkHistory,
)
from neighborly.components.character import (
    CanAge,
    CanGetPregnant,
    CharacterAgingConfig,
    GameCharacter,
    Gender,
    GenderValue,
    LifeStage,
    LifeStageValue,
)
from neighborly.components.factory import parse_operating_hour_str
from neighborly.components.relationship import Relationships
from neighborly.components.residence import Residence, ResidentialZoning
from neighborly.components.routine import Routine
from neighborly.components.shared import Active, Age, Lifespan, Location, Position2D
from neighborly.core.ai import MovementAI
from neighborly.core.ecs import GameObject, World
from neighborly.core.name_generation import TraceryNameFactory
from neighborly.core.status import add_status
from neighborly.engine import (
    BusinessArchetypeConfig,
    BusinessSpawnConfig,
    CharacterArchetypeConfig,
    CharacterSpawnConfig,
    NeighborlyEngine,
    ResidenceArchetypeConfig,
    ResidenceSpawnConfig,
)
from neighborly.plugins.defaults.ai import DefaultMovementModule
from neighborly.simulation import Plugin, Simulation
from neighborly.statuses.character import Unemployed


class BaseCharacterArchetype(CharacterArchetypeConfig):
    """Base factory class for constructing new characters"""

    def __init__(
        self,
        first_name: str = "first_name",
        last_name: str = "last_name",
        lifespan: int = 83,
        child_age: int = 0,
        adolescent_age: int = 13,
        young_adult_age: int = 18,
        adult_age: int = 30,
        senior_age: int = 65,
        spawn_frequency: int = 1,
        spouse_archetypes: Optional[List[str]] = None,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 3,
        child_archetypes: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            name="BaseCharacter",
            factory=BaseCharacterArchetype.create,
            spawn_config=CharacterSpawnConfig(
                spawn_frequency=spawn_frequency,
                spouse_archetypes=spouse_archetypes if spouse_archetypes else [],
                chance_spawn_with_spouse=chance_spawn_with_spouse,
                max_children_at_spawn=max_children_at_spawn,
                child_archetypes=child_archetypes if child_archetypes else [],
            ),
            options={
                "first_name": first_name,
                "last_name": last_name,
                "lifespan": lifespan,
                "child_age": child_age,
                "adolescent_age": adolescent_age,
                "young_adult_age": young_adult_age,
                "adult_age": adult_age,
                "senior_age": senior_age,
            },
        )

    @staticmethod
    def create(world: World, **kwargs: Any) -> GameObject:
        # Perform calculations first and return the base character GameObject
        name_generator = world.get_resource(TraceryNameFactory)

        first_name: str = name_generator.get_name(kwargs["first_name"])
        last_name: str = name_generator.get_name(kwargs["last_name"])
        lifespan: int = kwargs["lifespan"]
        child_age: int = kwargs["child_age"]
        adolescent_age: int = kwargs["adolescent_age"]
        young_adult_age: int = kwargs["young_adult_age"]
        adult_age: int = kwargs["adult_age"]
        senior_age: int = kwargs["senior_age"]

        gameobject = world.spawn_gameobject(
            [
                Active(),
                GameCharacter(first_name, last_name),
                Routine(),
                Age(),
                WorkHistory(),
                CharacterAgingConfig(
                    lifespan=lifespan,
                    child_age=child_age,
                    adolescent_age=adolescent_age,
                    young_adult_age=young_adult_age,
                    adult_age=adult_age,
                    senior_age=senior_age,
                ),
                Relationships(),
                MovementAI(DefaultMovementModule()),
            ]
        )

        rng = world.get_resource(random.Random)

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
                    BaseCharacterArchetype._life_stage_from_age(
                        gameobject.get_component(CharacterAgingConfig), age
                    )
                )
            )
        else:
            gameobject.add_component(
                LifeStage(BaseCharacterArchetype._life_stage_from_str(life_stage))
            )
            gameobject.add_component(
                Age(
                    BaseCharacterArchetype._generate_age_from_life_stage(
                        rng,
                        gameobject.get_component(CharacterAgingConfig),
                        life_stage,
                    )
                )
            )

        # gender
        gender: GenderValue = rng.choice(list(GenderValue))
        gameobject.add_component(Gender(gender))

        # Initialize employment status
        if life_stage == "young_adult" or life_stage == "adult":
            gameobject.add_component(InTheWorkforce())
            add_status(world, gameobject, Unemployed(30))

        if BaseCharacterArchetype._fertility_from_gender(rng, gender):
            gameobject.add_component(CanGetPregnant())

        # name
        first_name, last_name = BaseCharacterArchetype._generate_name_from_gender(
            world.get_resource(TraceryNameFactory), gender
        )
        character_component = gameobject.get_component(GameCharacter)
        character_component.first_name = first_name
        character_component.last_name = last_name

        engine = world.get_resource(NeighborlyEngine)

        component_data: List[Dict[str, Any]] = kwargs.get("components", [])
        for entry in component_data:
            component_factory = engine.get_component_info(entry["name"]).factory
            gameobject.add_component(
                component_factory.create(world, **entry.get("options", {}))
            )

        return gameobject

    @staticmethod
    def _life_stage_from_age(
        aging_config: CharacterAgingConfig, age: int
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

    @staticmethod
    def _generate_age_from_life_stage(
        rng: random.Random, aging_config: CharacterAgingConfig, life_stage: str
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

    @staticmethod
    def _life_stage_from_str(life_stage: str) -> LifeStageValue:
        """Return the proper component given the life stage"""
        stages = {
            "child": LifeStageValue.Child,
            "adolescent": LifeStageValue.Adolescent,
            "young_adult": LifeStageValue.YoungAdult,
            "adult": LifeStageValue.Adult,
            "senior": LifeStageValue.Senior,
        }
        return stages[life_stage]

    @staticmethod
    def _fertility_from_gender(rng: random.Random, gender: GenderValue) -> bool:
        """Return true if this character can get pregnant given their gender"""
        if gender == GenderValue.Female:
            return rng.random() < 0.8
        elif gender == GenderValue.Male:
            return False
        else:
            return rng.random() < 0.5

    @staticmethod
    def _generate_name_from_gender(
        name_generator: TraceryNameFactory, gender: GenderValue
    ) -> Tuple[str, str]:
        """Generate a name for the character given their gender"""
        if gender == GenderValue.Male:
            first_name_category = "#masculine_first_name#"
        elif gender == GenderValue.Female:
            first_name_category = "#feminine_first_name#"
        else:
            first_name_category = "#first_name#"

        first_name = name_generator.get_name(first_name_category)
        last_name = name_generator.get_name("#family_name#")

        return first_name, last_name


class BaseBusinessArchetype(BusinessArchetypeConfig):
    """
    Shared information about all businesses that
    have this type
    """

    def __init__(
        self,
        name: str = "BaseBusiness",
        business_type: Optional[Type[IBusinessType]] = None,
        name_format: str = "Business",
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
        super().__init__(
            name=name,
            factory=BaseBusinessArchetype.create,
            spawn_config=BusinessSpawnConfig(
                spawn_frequency=spawn_frequency,
                max_instances=max_instances,
                min_population=min_population,
                year_available=year_available,
                year_obsolete=year_obsolete,
            ),
            options={
                "business_type": business_type,
                "hours": hours,
                "name_format": name_format,
                "owner_type": owner_type,
                "employee_types": employee_types if employee_types else {},
                "services": services if services else [],
                "average_lifespan": average_lifespan,
            },
        )

    @staticmethod
    def create(world: World, **kwargs: Any) -> GameObject:
        name_generator = world.get_resource(TraceryNameFactory)

        service_names: List[str] = kwargs["services"]
        business_type: Optional[Type[IBusinessType]] = kwargs.get("business_type")
        name_format: str = kwargs["name_format"]
        hours: str = kwargs["hours"]
        owner_type: Optional[str] = kwargs.get("owner_type")
        employee_types: Dict[str, int] = kwargs["employee_types"]
        average_lifespan: int = kwargs["average_lifespan"]

        services: Set[ServiceType] = set()

        for service in service_names:
            services.add(ServiceTypes.get(service))

        gameobject = world.spawn_gameobject(
            [
                Business(
                    name=name_generator.get_name(name_format),
                    operating_hours=parse_operating_hour_str(hours),
                    owner_type=owner_type,
                    open_positions=employee_types,
                ),
                Age(0),
                Services(services),
                Position2D(),
                Location(),
                Lifespan(average_lifespan),
            ]
        )

        if business_type:
            gameobject.add_component(business_type())

        engine = world.get_resource(NeighborlyEngine)

        component_data: List[Dict[str, Any]] = kwargs.get("components", [])
        for entry in component_data:
            component_factory = engine.get_component_info(entry["name"]).factory
            gameobject.add_component(
                component_factory.create(world, **entry.get("options", {}))
            )

        return gameobject


class BaseResidenceArchetype(ResidenceArchetypeConfig):
    def __init__(
        self,
        zoning: ResidentialZoning = ResidentialZoning.SingleFamily,
        spawn_frequency: int = 1,
    ) -> None:
        super().__init__(
            name="BaseResidence",
            factory=BaseResidenceArchetype.create,
            spawn_config=ResidenceSpawnConfig(
                spawn_frequency=spawn_frequency, residential_zoning=zoning
            ),
            options={},
        )

    @staticmethod
    def create(world: World, **kwargs: Any) -> GameObject:
        gameobject = world.spawn_gameobject([Residence(), Location(), Position2D()])

        engine = world.get_resource(NeighborlyEngine)

        component_data: List[Dict[str, Any]] = kwargs.get("components", [])
        for entry in component_data:
            component_factory = engine.get_component_info(entry["name"]).factory
            gameobject.add_component(
                component_factory.create(world, **entry.get("options", {}))
            )

        return gameobject


class DefaultArchetypesPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        # Add archetypes
        sim.engine.character_archetypes.add(BaseCharacterArchetype())
        sim.engine.business_archetypes.add(BaseBusinessArchetype())
        sim.engine.residence_archetypes.add(BaseResidenceArchetype())
