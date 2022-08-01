import random
from pprint import pprint
from typing import Generator, List, Protocol, TypeVar

from neighborly.core.character import (
    AgingConfig,
    CharacterDefinition,
    CharacterName,
    FamilyGenerationOptions,
    GameCharacter,
    GenerationConfig,
)
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    ILifeEventCallback,
    LifeEvent,
    check_gameobject_preconditions,
    handle_gameobject_effects,
)
from neighborly.core.name_generation import get_name
from neighborly.core.relationship import RelationshipModifier
from neighborly.core.social_network import Relationship, RelationshipNetwork
from neighborly.core.tags import Tag
from neighborly.core.time import SimDateTime
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig

BASE_CHARACTER_DEF = CharacterDefinition(
    name="BaseCharacter",
    aging=AgingConfig(
        lifespan=85,
        life_stages={
            "child": 0,
            "adolescent": 13,
            "young_adult": 18,
            "adult": 30,
            "elder": 65,
        },
    ),
    generation=GenerationConfig(
        first_name="#first_name#",
        last_name="#last_name#",
        family=FamilyGenerationOptions(
            probability_spouse=0.5, probability_children=0.3, num_children=(0, 3)
        ),
    ),
)

HUMAN_CHARACTER_DEF = CharacterDefinition.create({"name": "Human"}, BASE_CHARACTER_DEF)
ANDROID_CHARACTER_DEF = CharacterDefinition.create(
    {"name": "Android"}, BASE_CHARACTER_DEF
)


class LifeEvenRulePatternFn(Protocol):
    def __call__(self, world: World) -> LifeEvent:
        raise NotImplementedError


class LifeEvenRulePreconditionFn(Protocol):
    def __call__(self, event: LifeEvent) -> bool:
        raise NotImplementedError


class LifeEventRuleEffectFn(Protocol):
    def __call__(self, event: LifeEvent) -> None:
        raise NotImplementedError


class LifeEventRule:

    __slots__ = (
        "name",
        "description",
        "pattern_fn",
        "probability",
        "precondition_fn",
        "effect_fn",
    )

    def __init__(
        self,
        name: str,
        description: str,
        probability: float,
        pattern_fn: LifeEvenRulePatternFn,
        precondition_fn: LifeEvenRulePreconditionFn,
        effect_fn: LifeEventRuleEffectFn,
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.probability: float = probability
        self.pattern_fn: LifeEvenRulePatternFn = pattern_fn
        self.precondition_fn: LifeEvenRulePreconditionFn = precondition_fn
        self.effect_fn: LifeEventRuleEffectFn = effect_fn


def say_hello(gameobject: GameObject, event: LifeEvent) -> bool:
    print("Hello, World")
    return True


def add_friendship_buff(value: int) -> ILifeEventCallback:
    def cb(gameobject: GameObject, event: LifeEvent) -> bool:
        relationship: Relationship = event.data["relationship"]
        relationship.add_modifier(
            RelationshipModifier(
                "Friendly",
                "This character is friendly to others",
                friendship_boost=value,
            )
        )
        print("Added relationship buff")
        return True

    return cb


def reduce_friendliness_to_women(value: int) -> ILifeEventCallback:
    def cb(gameobject: GameObject, event: LifeEvent) -> bool:
        relationship: Relationship = event.data["relationship"]

        other = relationship.target

        target = gameobject.world.get_gameobject(other).get_component(GameCharacter)

        if "Woman" in target.tags:
            relationship.add_modifier(
                RelationshipModifier(
                    "Misogynist",
                    "This character is does not like women",
                    friendship_boost=value,
                )
            )
            print("Added relationship buff against women")
        return True

    return cb


always_friendly_tag = Tag(
    name="Always Friendly",
    description="This character is always friends to everyone even enemies",
    event_effects={"createRelationship": add_friendship_buff(10)},
)

woman_tag = Tag(name="Woman", description="This character is a woman")

misogynist = Tag(
    name="Misogynist",
    description="This character is not friendly to women",
    event_effects={"createRelationship": reduce_friendliness_to_women(-10)},
)


def handle_socialize(gameobject: GameObject, event: LifeEvent) -> bool:
    # Get the other character
    characters: list[GameObject] = [*event.data["characters"]]
    characters.remove(gameobject)
    other = characters[0]

    # Check if there is an existing relationship
    relationship_network = gameobject.world.get_resource(RelationshipNetwork)
    if not relationship_network.has_connection(gameobject.id, other.id):
        relationship = Relationship(gameobject.id, other.id)
        relationship_network.add_connection(gameobject.id, other.id, relationship)
        handle_gameobject_effects(
            gameobject,
            LifeEvent(
                event_type="create-relationship",
                timestamp=gameobject.world.get_resource(SimDateTime).to_iso_str(),
                relationship=relationship,
            ),
        )

    return True


_T = TypeVar("_T")


def chunk_list(lst: List[_T], n: int) -> Generator[List[_T], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def socialize_system(world: World, **kwargs) -> None:
    for pair in chunk_list(world.get_component(GameCharacter), 2):
        character_0 = pair[0][1].gameobject
        character_1 = pair[1][1].gameobject

        # choose an interaction type
        interaction_type = random.choice(
            ["neutral", "friendly", "flirty", "bad", "boring", "good", "exciting"]
        )

        socialize_event = LifeEvent(
            event_type="Socialize",
            timestamp=world.get_resource(SimDateTime).to_iso_str(),
            interaction=interaction_type,
            characters=[character_0, character_1],
        )

        character_0_consent = check_gameobject_preconditions(
            character_0, socialize_event
        )
        character_1_consent = check_gameobject_preconditions(
            character_1, socialize_event
        )

        if character_0_consent and character_1_consent:
            handle_gameobject_effects(character_0, socialize_event)
            handle_gameobject_effects(character_1, socialize_event)


def create_child(
    engine: NeighborlyEngine, pregnant_parent: GameObject, other_parent: GameObject
) -> GameObject:

    # Choose which parent to inherit last name from
    last_name = pregnant_parent.get_component(GameCharacter).name.surname

    # Choose which parent to inherit archetype / definition from
    character_def = (
        engine.rng.choice([pregnant_parent, other_parent])
        .get_component(GameCharacter)
        .character_def
    )

    first_name = get_name(character_def.generation.first_name)

    baby = GameObject(
        components=[
            GameCharacter(
                character_def,
                CharacterName(first_name, last_name),
                0,
            )
        ]
    )

    return baby


def main():

    DEFAULT_NEIGHBORLY_CONFIG = NeighborlyConfig(
        simulation=SimulationConfig(
            seed=random.randint(0, 999999),
            hours_per_timestep=6,
            start_date="0000-00-00T00:00.000z",
            end_date="0100-00-00T00:00.000z",
        ),
        plugins=["neighborly.plugins.default_plugin"],
    )

    sim = Simulation(DEFAULT_NEIGHBORLY_CONFIG)
    world = sim.world
    world.add_system(socialize_system)

    tanjiro = GameObject(
        components=[
            GameCharacter(
                HUMAN_CHARACTER_DEF,
                CharacterName("Tanjiro", "Kamado"),
                13,
                tags=[misogynist],
                events={
                    "greet": {
                        "effects": [say_hello],
                    },
                    "socialize": {
                        "effects": [handle_socialize],
                    },
                },
            ),
        ]
    )

    world.add_gameobject(tanjiro)

    pprint(tanjiro.to_dict())

    delores = GameObject(
        components=[
            GameCharacter(
                ANDROID_CHARACTER_DEF,
                CharacterName("Delores", "Abernathy"),
                30,
                tags=[woman_tag],
                events={
                    "greet": {
                        "effects": [say_hello],
                    },
                    "socialize": {
                        "effects": [handle_socialize],
                    },
                },
            )
        ]
    )

    world.add_gameobject(delores)

    event = LifeEvent(event_type="greet", timestamp="")

    handle_gameobject_effects(delores, event)
    handle_gameobject_effects(tanjiro, event)

    for _ in range(10):
        print(
            create_child(world.get_resource(NeighborlyEngine), delores, tanjiro)
            .get_component(GameCharacter)
            .name
        )

    print("Done")


if __name__ == "__main__":
    main()
