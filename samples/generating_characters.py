import random
from neighborly.core.character import CharacterDefinition
from neighborly.core.character import (
    GenerationConfig,
    FamilyGenerationOptions,
    LifeCycleConfig,
)
from neighborly.core.character import generate_character
from neighborly.core.rng import DefaultRNG
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig

BASE_CHARACTER_TYPE = CharacterDefinition(
    name="BaseCharacter",
    lifecycle=LifeCycleConfig(
        lifespan=85,
        life_stages={
            "child": 0,
            "teen": 13,
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

DEFAULT_NEIGHBORLY_CONFIG = NeighborlyConfig(
    simulation=SimulationConfig(
        seed=random.randint(0, 999999),
        hours_per_timestep=6,
        start_date="0000-00-00T00:00.000z",
        end_date="0100-00-00T00:00.000z",
    ),
    plugins=["neighborly.plugins.default_plugin"],
)


def main():
    sim = Simulation(DEFAULT_NEIGHBORLY_CONFIG)
    print(generate_character(BASE_CHARACTER_TYPE, sim.get_engine().get_rng()))
    # print(create_family(BASE_CHARACTER_TYPE, DefaultRNG()))


if __name__ == "__main__":
    main()
