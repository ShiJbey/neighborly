import random
import numpy as np

from neighborly.core.authoring import AbstractConstructor, AbstractFactory, CreationData
from neighborly.core.business import Business
from neighborly.core.character.character import GameCharacter


class GameCharacterFactory(AbstractConstructor):
    """
    Default factory for constructing instances of
    GameCharacters.
    """

    def create(self, cls_type, creation_data) -> GameCharacter:
        """Create a new instance of a character"""

        age_range: str = kwargs.get("age_range", "adult")
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

        values = generate_character_values()

        character = cls(
            config,
            CharacterName(firstname, surname),
            age,
            max_age,
            gender,
            values,
            set(random.sample(list(Gender), random.randint(0, 2))),
        )

        return character

    @staticmethod
    def generate_adult_age(config: CharacterConfig) -> float:
        return np.random.uniform(
            config.lifecycle.adult_age, config.lifecycle.adult_age + 15
        )


class BusinessFactory(AbstractFactory[Business]):
    ...
