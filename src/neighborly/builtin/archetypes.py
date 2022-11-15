from typing import Optional

from neighborly.builtin.components import (
    Adult,
    Age,
    CanAge,
    CanGetPregnant,
    Child,
    Elder,
    Female,
    Lifespan,
    LifeStages,
    Male,
    NonBinary,
    Teen,
)
from neighborly.core.archetypes import BaseCharacterArchetype
from neighborly.core.business import InTheWorkforce, Unemployed
from neighborly.core.character import CharacterName, LifeStageAges
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine


class HumanArchetype(BaseCharacterArchetype):
    __slots__ = "life_stage_ages", "lifespan"

    def __init__(
        self,
        life_stage_ages: Optional[LifeStageAges] = None,
        lifespan: int = 73,
        spawn_frequency: int = 1,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 0,
    ) -> None:
        super().__init__(
            spawn_frequency=spawn_frequency,
            chance_spawn_with_spouse=chance_spawn_with_spouse,
            max_children_at_spawn=max_children_at_spawn,
        )
        self.life_stage_ages: LifeStageAges = (
            life_stage_ages
            if life_stage_ages is not None
            else {
                "child": 0,
                "teen": 13,
                "young_adult": 18,
                "adult": 30,
                "elder": 65,
            }
        )
        self.lifespan: int = lifespan

    def create(self, world: World, **kwargs) -> GameObject:
        # Perform calculations first and return the base character GameObject
        gameobject = super().create(world, **kwargs)

        engine = world.get_resource(NeighborlyEngine)

        life_stage: str = kwargs.get("life_stage", "young_adult")
        age: Optional[int] = kwargs.get("age")

        if "life_stage_ages" in kwargs:
            self.life_stage_ages = kwargs["life_stage_ages"]

        gameobject.add_component(Lifespan(self.lifespan))
        gameobject.add_component(CanAge())
        gameobject.add_component(LifeStages(self.life_stage_ages))

        if age is not None:
            # Age takes priority over life stage if both are given
            gameobject.add_component(Age(age))
            gameobject.add_component(self._life_stage_from_age(age))
        else:
            gameobject.add_component(self._life_stage_from_str(life_stage))
            gameobject.add_component(
                Age(self._generate_age_from_life_stage(world, life_stage))
            )

        # gender
        gender: Component = engine.rng.choice([Male, Female, NonBinary])()
        gameobject.add_component(gender)

        # Initialize employment status
        if life_stage == "young_adult" or life_stage == "adult":
            gameobject.add_component(InTheWorkforce())
            gameobject.add_component(Unemployed())

        if self._fertility_from_gender(world, gender):
            gameobject.add_component(CanGetPregnant())

        # name
        gameobject.add_component(self._generate_name_from_gender(world, gender))

        return gameobject

    def _life_stage_from_age(self, age: int) -> Component:
        """Determine the life stage of a character given an age"""
        if 0 <= age < self.life_stage_ages["teen"]:
            return Child()
        elif self.life_stage_ages["teen"] <= age < self.life_stage_ages["young_adult"]:
            return Teen()
        elif self.life_stage_ages["young_adult"] <= age < self.life_stage_ages["adult"]:
            return Adult()
        elif self.life_stage_ages["adult"] <= age < self.life_stage_ages["elder"]:
            return Adult()
        else:
            return Elder()

    def _generate_age_from_life_stage(self, world: World, life_stage: str) -> int:
        """Generates a random age given a life stage"""
        engine = world.get_resource(NeighborlyEngine)

        if life_stage == "child":
            return engine.rng.randint(0, self.life_stage_ages["teen"] - 1)
        elif life_stage == "teen":
            return engine.rng.randint(
                self.life_stage_ages["teen"],
                self.life_stage_ages["young_adult"] - 1,
            )
        elif life_stage == "young_adult":
            return engine.rng.randint(
                self.life_stage_ages["young_adult"],
                self.life_stage_ages["adult"] - 1,
            )
        elif life_stage == "adult":
            return engine.rng.randint(
                self.life_stage_ages["adult"],
                self.life_stage_ages["elder"] - 1,
            )
        else:
            return self.life_stage_ages["elder"]

    def _life_stage_from_str(self, life_stage: str) -> Component:
        """Return the proper component given the life stage"""
        if life_stage == "child":
            return Child()
        elif life_stage == "teen":
            return Teen()
        elif life_stage == "young_adult":
            return Adult()
        elif life_stage == "adult":
            return Adult()
        else:
            return Elder()

    def _fertility_from_gender(self, world: World, gender: Component) -> bool:
        """Return true if this character can get pregnant given their gender"""
        engine = world.get_resource(NeighborlyEngine)

        if type(gender) == Female:
            return engine.rng.random() < 0.8
        elif type(gender) == Male:
            return False
        else:
            return engine.rng.random() < 0.4

    def _generate_name_from_gender(
        self, world: World, gender: Component
    ) -> CharacterName:
        """Generate a name for the character given their gender"""
        engine = world.get_resource(NeighborlyEngine)

        if type(gender) == Male:
            first_name_category = "#masculine_first_name#"
        elif type(gender) == Female:
            first_name_category = "#feminine_first_name#"
        else:
            first_name_category = "#first_name#"

        return CharacterName(
            engine.name_generator.get_name(first_name_category),
            engine.name_generator.get_name("#family_name#"),
        )
