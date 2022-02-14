from neighborly.ai import behavior_utils
from neighborly.loaders import YamlDataLoader
from neighborly.plugins import default_plugin
from neighborly.simulation import Simulation, SimulationConfig

STRUCTURES = """
    Places:
        Space Casino:
            Location:
                activities: ["gambling", "drinking", "eating", "socializing"]
        Mars:
            Location:
                activities: ["reading", "relaxing"]
        Kamino:
            Location:
                activities: ["recreation", "studying"]
    """


def main():
    config = SimulationConfig(hours_per_timestep=4)
    sim = Simulation(config)
    default_plugin.initialize_plugin(sim.get_engine())
    YamlDataLoader(str_data=STRUCTURES).load(sim.get_engine())

    character_1 = sim.get_engine().create_character(sim.world, "Civilian")
    character_2 = sim.get_engine().create_character(sim.world, "Civilian")

    loc1 = sim.get_engine().create_place(sim.world, "Space Casino")
    loc2 = sim.get_engine().create_place(sim.world, "Mars")
    loc3 = sim.get_engine().create_place(sim.world, "Kamino")

    print("=== LOCATIONS ==")
    print(f"Space casino: {loc1}")
    print(f"Mars: {loc2}")
    print(f"Kamino: {loc3}")

    print("=== SIMULATION ==")
    for _ in range(100):
        sim.step()

    print(sim.world.components_for_entity(character_1))

    print(behavior_utils.get_relationship_net(sim.world).get_connection(character_1, character_2))
    print(behavior_utils.get_relationship_net(sim.world).get_connection(character_2, character_1))


if __name__ == "__main__":
    main()
