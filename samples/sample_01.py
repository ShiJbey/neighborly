from neighborly.loaders import load_structure_definitions
from neighborly.plugins import default_plugin
from neighborly.simulation import Simulation, SimulationConfig
from neighborly.core.engine import NeighborlyEngine

STRUCTURES = """
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
    config = SimulationConfig(hours_per_timestep=4)
    sim = Simulation(config)
    engine = NeighborlyEngine()

    engine.create_character(sim.world)
    engine.create_character(sim.world)

    loc1 = engine.create_place(sim.world, "Space Casino")
    loc2 = engine.create_place(sim.world, "Mars")
    loc3 = engine.create_place(sim.world, "Kamino")

    print("=== LOCATIONS ==")
    print(f"Space casino: {loc1}")
    print(f"Mars: {loc2}")
    print(f"Kamino: {loc3}")

    print("=== SIMULATION ==")
    for _ in range(100):
        sim.step()


if __name__ == "__main__":
    main()
