import random

import numpy as np

import neighborly.core.name_generation as name_gen
from neighborly.core.authoring import AbstractFactory, ComponentSpec
from neighborly.core.business import Business, BusinessConfig
from neighborly.core.character.character import (
    GameCharacter,
    CharacterConfig,
    Gender,
    CharacterName,
)
from neighborly.core.character.values import CharacterValues, generate_character_values
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine


class GameCharacterFactory(AbstractFactory):
    """
    Default factory for constructing instances of
    GameCharacters.
    """

    def __init__(self) -> None:
        super().__init__("GameCharacter")

    def create(self, spec: ComponentSpec) -> GameCharacter:
        """Create a new instance of a character"""

        config: CharacterConfig = CharacterConfig(**spec.get_attributes())

        age_range: str = spec.get_attributes().get("age_range", "adult")
        if age_range == "child":
            age: float = float(random.randint(3, config.lifecycle.adult_age))
        elif age_range == "adult":
            age: float = float(
                random.randint(config.lifecycle.adult_age, config.lifecycle.senior_age)
            )
        else:
            age: float = float(
                random.randint(
                    config.lifecycle.senior_age, config.lifecycle.lifespan_mean
                )
            )

        gender: Gender = random.choice(list(Gender))

        name_rule: str = (
            config.gender_overrides[str(gender)].name
            if str(gender) in config.gender_overrides
            else config.name
        )

        firstname, surname = tuple(name_gen.get_name(name_rule).split(" "))

        max_age: float = max(
            age + 1,
            np.random.normal(
                config.lifecycle.lifespan_mean, config.lifecycle.lifespan_std
            ),
        )

        values: CharacterValues = generate_character_values()

        character = GameCharacter(
            config,
            CharacterName(firstname, surname),
            age,
            max_age,
            gender,
            values,
            tuple(random.sample(list(Gender), random.randint(0, 2))),
        )

        return character

    @staticmethod
    def generate_adult_age(config: CharacterConfig) -> float:
        return np.random.uniform(
            config.lifecycle.adult_age, config.lifecycle.adult_age + 15
        )


class BusinessFactory(AbstractFactory):
    """Create instances of the default business component"""

    def __init__(self) -> None:
        super().__init__("Business")

    def create(self, spec: ComponentSpec) -> Business:
        name = name_gen.get_name(spec["name"])

        conf = BusinessConfig(
            business_type=spec["business type"],
            name=spec["name"]
        )

        return Business(conf, name)


class RoutineFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Routine")

    def create(self, spec: ComponentSpec) -> Routine:
        return Routine()


class LocationFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Location")

    def create(self, spec: ComponentSpec) -> Location:
        return Location(max_capacity=spec.get_attributes().get("max capacity", 9999), activities=spec["activities"])


class ResidenceFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Residence")

    def create(self, spec: ComponentSpec) -> Residence:
        return Residence()


class Position2DFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Position2D")

    def create(self, spec: ComponentSpec) -> Position2D:
        return Position2D()
