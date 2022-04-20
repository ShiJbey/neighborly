from enum import Enum
from typing import Dict, NamedTuple, Optional, Tuple, List, ClassVar, TypedDict, Any, Union

import numpy as np
from ordered_set import OrderedSet
from pydantic import BaseModel, Field, validator

from neighborly.core import name_generation as name_gen
from neighborly.core.activity import _activity_registry
from neighborly.core.character.values import CharacterValues, generate_character_values
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec
from neighborly.core.rng import RandNumGenerator
from neighborly.core.utils.utilities import parse_number_range


class AgeRanges(TypedDict):
    """Age range values for characters of a given type"""
    child: Tuple[int, int]
    teen: Tuple[int, int]
    young_adult: Tuple[int, int]
    adult: Tuple[int, int]
    senior: Tuple[int, int]


class LifeCycleConfig(BaseModel):
    """Configuration parameters for a characters lifecycle

    Fields
    ------
    can_age: bool
        Will his character's age change during th simulation
    can_die: bool
        Can this character die when it reaches its max age
    lifespan_mean: int
        Average lifespan of characters with this configuration
    lifespan_std: int
        Standard deviation of the lifespans of characters with this
        configuration
    adult_age: int
        Age that characters with thi config are considered adults
        in society
    romantic_feelings_age: int
        The age that characters start to develop romantic feelings
        for other characters
    """
    can_age: bool
    can_die: bool
    chance_of_death: float
    romantic_feelings_age: int
    marriageable_age: int
    age_ranges: AgeRanges

    @validator('age_ranges', pre=True)
    def convert_age_ranges_to_tuples(cls, v):
        if not isinstance(v, dict):
            raise TypeError("Attribute 'age_ranges' expected dict object")

        validated_dict = {}
        for key, value in v.items():
            if isinstance(value, str):
                validated_dict[key] = parse_number_range(value)
            else:
                validated_dict[key] = value
        return validated_dict


class FamilyGenerationOptions(BaseModel):
    """Options used when generating a family for a new character entering the town"""
    probability_spouse: float
    probability_children: float
    num_children: Tuple[int, int]

    @validator('num_children', pre=True)
    def convert_age_ranges_to_tuples(cls, v):
        if isinstance(v, str):
            return parse_number_range(v)
        return v


class GenerationConfig(BaseModel):
    """Parameters for generating new characters with this type"""
    first_name: str
    last_name: str
    family: FamilyGenerationOptions
    gender_weights: Dict[str, int] = Field(default_factory=dict)


class CharacterDefinition(BaseModel):
    """Configuration parameters for characters

    Fields
    ------
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    """

    _type_registry: ClassVar[Dict[str, 'CharacterDefinition']] = {}

    name: str
    lifecycle: LifeCycleConfig
    generation: GenerationConfig
    gender_overrides: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, options: Dict[str, Any], base: Optional['CharacterDefinition'] = None) -> 'CharacterDefinition':
        """Create a new Character type

        Parameters
        ----------
        options: dict[str, Any]
            data used to instantiate the CharacterType
        base: CharacterType
            Character type to base the new type off of
        """

        character_def = {}

        if base:
            character_def.update(base.dict())

        character_def.update(options)

        return CharacterDefinition(**character_def)

    @classmethod
    def register_type(cls, type_config: 'CharacterDefinition') -> None:
        """Registers a character config with the shared registry"""
        cls._type_registry[type_config.name] = type_config

    @classmethod
    def get_type(cls, name: str) -> 'CharacterDefinition':
        """Retrieve a CharacterConfig from the shared registry"""
        return cls._type_registry[name]


class CharacterName(NamedTuple):
    firstname: str
    surname: str

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class Gender(Enum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTRAL = "neutral"


class GameCharacter(Component):
    """The state of a single character within the world

    Attributes
    ----------
    character_def: CharacterType
        Configuration settings for the character
    name: CharacterName
        The character's name
    age: float
        The character's current age in years
    gender: Gender
        Loose gender identity for the character
    location: int
        Entity ID of the location where this character current is
    location_aliases: Dict[str, int]
        Maps string names to entity IDs of locations in the world
    likes: Tuple[str, ...]
        Names of activities that this character likes to do
    values: CharacterValues
        A characters beliefs/values in life (i.e. loyalty, family, wealth)
    """

    __slots__ = (
        "character_def",
        "alive",
        "name",
        "age",
        "gender",
        "can_get_pregnant",
        "location",
        "location_aliases",
        "values",
        "likes",
        "attracted_to"
    )

    def __init__(
            self,
            character_def: CharacterDefinition,
            name: CharacterName,
            age: float,
            gender: Gender,
            values: CharacterValues,
            attracted_to: Tuple[Gender, ...],
    ) -> None:
        super().__init__()
        self.character_def = character_def
        self.alive: bool = True
        self.name: CharacterName = name
        self.age: float = age
        self.gender: Gender = gender
        self.attracted_to: OrderedSet[Gender] = OrderedSet(attracted_to)
        self.location: Optional[int] = None
        self.location_aliases: Dict[str, int] = {}
        self.likes: Tuple[str, ...] = get_top_activities(values)
        self.values: CharacterValues = values

    def on_start(self) -> None:
        self.gameobject.set_name(str(self.name))

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            'character_def': self.character_def.name,
            'name': str(self.name),
            'alive': self.alive,
            'age': self.age,
            'gender': self.gender.value,
            'attracted_to': [g.value for g in self.attracted_to],
            'location': self.location,
            'location_aliases': self.location_aliases,
            'likes': self.likes,
            'values': self.values.traits.tolist(),
        }

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(name={}, age={}, gender={}, location={}, location_aliases={}, likes={}, {})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            self.gender,
            self.location,
            self.location_aliases,
            self.likes,
            str(self.values),
        )


def choose_gender(rng: RandNumGenerator, overrides: Optional[Dict[str, int]] = None) -> Gender:
    weights = [1 for _ in list(Gender)]
    if overrides:
        for i, g in enumerate(list(Gender)):
            if overrides.get(g.value):
                weights[i] = overrides[g.value]
    return Gender[rng.choices(list(Gender), weights)[0].name]


def create_character(
        character_type: CharacterDefinition,
        rng: RandNumGenerator,
        **kwargs
) -> GameCharacter:
    first_name = kwargs.get('first_name', name_gen.get_name(
        character_type.generation.first_name))
    last_name = kwargs.get('last_name', name_gen.get_name(
        character_type.generation.last_name))
    name = CharacterName(first_name, last_name)

    gender = kwargs.get('gender', choose_gender(rng))

    # generate an age
    age_range: Union[str, Tuple[int, int]] = kwargs.get(
        'age_range', character_type.lifecycle.age_ranges['adult'])

    age = -1
    if isinstance(age_range, str):
        if age_range in character_type.lifecycle.age_ranges:
            range_tuple = character_type.lifecycle.age_ranges[age_range]  # type: ignore
            age = rng.randint(range_tuple[0], range_tuple[1])
        else:
            ValueError(
                f"Given age range ({age_range}) is not one of (child, teen, young adult, adult, senior)")
    else:
        age = rng.randint(age_range[0], age_range[1])

    if age == -1:
        raise RuntimeError("Age never set")

    values: CharacterValues = generate_character_values(rng)

    attracted_to = kwargs.get('attracted_to', tuple(
        rng.sample(list(Gender), rng.randint(0, 2))))

    return GameCharacter(
        character_def=character_type,
        name=name,
        age=float(age),
        gender=gender,
        values=values,
        attracted_to=attracted_to,
    )


class GameCharacterFactory(AbstractFactory):
    """
    Default factory for constructing instances of
    GameCharacters.
    """

    def __init__(self) -> None:
        super().__init__("GameCharacter")

    def create(self, spec: ComponentSpec, **kwargs) -> GameCharacter:
        """Create a new instance of a character"""
        return create_character(
            character_type=CharacterDefinition.get_type(spec['character_def']),
            **kwargs
        )


def create_family(
        character_type: CharacterDefinition,
        rng: RandNumGenerator,
        **kwargs
) -> Dict[str, List[GameCharacter]]:
    adults: List[GameCharacter] = []
    children: List[GameCharacter] = []

    adult_0 = create_character(character_type, rng, age_range='young_adult')
    adult_1 = create_character(character_type, rng, age_range='young_adult', last_name=adult_0.name.surname,
                               attracted_to=[adult_0.gender])

    adults.append(adult_0)
    adults.append(adult_1)

    num_children = kwargs.get('n_children',
                              rng.randint(0,
                                          int(min(adult_0.age,
                                                  adult_1.age) - character_type.lifecycle.marriageable_age)))

    for _ in range(num_children):
        child = create_character(
            character_type, rng, age_range='child', last_name=adult_0.name.surname)
        children.append(child)

    return {'adults': adults, 'children': children}


def get_top_activities(
        character_values: CharacterValues, n: int = 3
) -> Tuple[str, ...]:
    """Return the top activities a character would enjoy given their values"""

    scores: List[Tuple[int, str]] = []

    for name, activity in _activity_registry.items():
        score: int = int(np.dot(character_values.traits,
                                activity.character_traits.traits))
        scores.append((score, name))

    return tuple(
        [
            activity_score[1]
            for activity_score in sorted(scores, key=lambda s: s[0], reverse=True)
        ][:n]
    )
