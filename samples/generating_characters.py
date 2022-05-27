import random
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject
from neighborly.loaders import YamlDataLoader
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig
from neighborly.core.life_event import (
    EventCallbackDatabase,
    LifeEvent,
    event_effect,
    handle_gameobject_effects,
)

CHARACTER_DATA = """
CharacterDefinitions:
  - name: Human
    generation:
      first_name: "#first_name#"
      last_name: "#last_name#"
      family:
        probability_spouse: 0.5
        probability_children: 0.5
        num_children: "0-2"
    lifecycle:
      lifespan: 85
      life_stages:
        child: 0
        adolescent: 13
        young_adult: 18
        adult: 30
        elder: 85
    events:
      marriage:
        effects: [on_married_behavior]
      child-birth:
        effects: [on_child_birth_behavior]
      move:
        effects: [on_move_behavior]
      custom-event:
        effects: [on_custom_event]
Characters:
  - name: Human
    components:
      - type: GameCharacter
        options:
          character_def: Human
"""

DEFAULT_NEIGHBORLY_CONFIG = NeighborlyConfig(
    simulation=SimulationConfig(
        seed=random.randint(0, 999999),
        hours_per_timestep=6,
        start_date="0000-00-00T00:00.000z",
        end_date="0100-00-00T00:00.000z",
    ),
    plugins=["neighborly.plugins.default_plugin"],
)


def on_married_behavior(gameobject: GameObject, event: LifeEvent) -> bool:
    print("I'm Got Married!")
    return True


def on_child_birth_behavior(gameobject: GameObject, event: LifeEvent) -> bool:
    print("I had a child!")
    return True


def on_move_behavior(gameobject: GameObject, event: LifeEvent) -> bool:
    print("I moved to a new house!")
    return True


@event_effect("on_custom_event")
def on_custom_event(gameobject: GameObject, event: LifeEvent) -> bool:
    if not isinstance(event, CustomLifeEvent):
        raise TypeError(f"Expected CustomLifeEvent but was {type(event)}")
    print(str(event))
    return True


def setup(sim: Simulation):
    EventCallbackDatabase.register_effect("on_married_behavior", on_married_behavior)
    EventCallbackDatabase.register_effect(
        "on_child_birth_behavior", on_child_birth_behavior
    )
    EventCallbackDatabase.register_effect("on_move_behavior", on_move_behavior)
    YamlDataLoader(str_data=CHARACTER_DATA).load(sim.get_engine())


class CustomLifeEvent(LifeEvent):
    event_type = "custom-event"

    def __init__(self, timestamp: str, character_id: int, character_name: str) -> None:
        super().__init__(timestamp)
        self.character_id: int = character_id
        self.character_name: str = character_name

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def __str__(self) -> str:
        return f"({self.timestamp}): Custom event happened to {self.character_name}"


def main():
    sim = Simulation(DEFAULT_NEIGHBORLY_CONFIG)

    setup(sim)

    character = sim.get_engine().create_character("Human")

    print(character.get_component(GameCharacter))

    handle_gameobject_effects(
        character,
        CustomLifeEvent(
            "May 26, 2022",
            character.id,
            str(character.get_component(GameCharacter).name),
        ),
    )
    # print(create_family(BASE_CHARACTER_TYPE, DefaultRNG()))


if __name__ == "__main__":
    main()
