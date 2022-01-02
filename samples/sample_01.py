from neighborly.core.character import CharacterConfig
from neighborly.simulation.simulation import SimulationConfig, Simulation
from neighborly.core.ecs_manager import create_character, register_character_config


def main():
    config = SimulationConfig(seed='sample_01')
    sim = Simulation(config)

    register_character_config('default', CharacterConfig())

    character_1 = create_character(sim.world, )


if __name__ == "__main__":
    main()
