from neighborly.core.character.character import CharacterConfig
from neighborly.plugins import default_plugin
from neighborly.simulation import SimulationConfig, Simulation
from neighborly.core.ecs_manager import create_character, register_character_config
from neighborly.authoring import load_structure_definitions
from neighborly.core.ecs_manager import create_structure


STRUCTURES = \
    """
    Space Casino:
        activities: ["gambling", "drinking", "eating", "socializing"]
    Mars:
        activities: ["reading", "relaxing"]
    Kamino:
        activities: ["recreation", "studying"]
    """


def main():
    default_plugin.initialize_plugin()
    load_structure_definitions(yaml_str=STRUCTURES)
    config = SimulationConfig(hours_per_timstep=4)
    sim = Simulation(config)

    register_character_config('default', CharacterConfig())

    character_1_id, character_1 = create_character(sim.world)
    character_2_id, character_2 = create_character(sim.world)

    print("=== CHARACTERS ==")
    print(character_1_id, character_1)
    print(character_2_id, character_2)

    loc1 = create_structure(sim.world, "Space Casino")
    loc2 = create_structure(sim.world, "Mars")
    loc3 = create_structure(sim.world, "Kamino")

    print("=== LOCATIONS ==")
    print(f"Space casino: {loc1}")
    print(f"Mars: {loc2}")
    print(f"Kamino: {loc3}")

    print("=== SIMULATION ==")
    for _ in range(100):
        sim.step()
        # print(f"{str(character_1.name)} Location: {character_1.location}")
        # print(f"{str(character_2.name)} Location: {character_2.location}")

    if character_2_id in character_1.relationships:
        print(character_1.relationships[character_2_id])


if __name__ == "__main__":
    main()
