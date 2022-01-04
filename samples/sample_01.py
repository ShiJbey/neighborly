from neighborly.core.character import CharacterConfig, GameCharacter
from neighborly.simulation.simulation import SimulationConfig, Simulation
from neighborly.core.ecs_manager import create_character, register_character_config
from neighborly.core.location import Location
from neighborly.core.gameobject import GameObject
import neighborly.theming.plugins.default as default_plugin


def main():
    default_plugin.initialize_plugin()

    config = SimulationConfig(seed='sample_01')
    sim = Simulation(config)

    register_character_config('default', CharacterConfig())

    character_1_id, character_1 = create_character(sim.world)
    character_2_id, character_2 = create_character(sim.world)

    loc1 = sim.world.create_entity(GameObject("Space Casino"), Location())
    loc2 = sim.world.create_entity(GameObject("Mars"), Location())
    loc3 = sim.world.create_entity(GameObject("Kamino"), Location())

    print(f"Space casino: {loc1}")
    print(f"Mars: {loc2}")
    print(f"Kamino: {loc3}")

    for _ in range(10):
        sim.step()
        print(character_1)
        print(character_2)

        if character_2_id in character_1.relationships:
            print(character_1.relationships[character_2_id])


if __name__ == "__main__":
    main()
