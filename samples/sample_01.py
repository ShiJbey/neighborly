from neighborly.loaders import YamlDataLoader
from neighborly.plugins import default_plugin
from neighborly.simulation import Simulation, SimulationConfig

STRUCTURES = """
    Places:
        - name: Space Casino
          components:
            - type: Location
              options:
                activities: ["Gambling", "Drinking", "Eating", "Socializing"]
        - name: Mars
          components:
            - type: Location
              options:
                activities: ["Reading", "Relaxing"]
        - name: Kamino
          components:
            - type: Location
              options:
                activities: ["Recreation", "Studying"]
    """


def main():
    config = SimulationConfig(hours_per_timestep=4)
    sim = Simulation.create(config)
    default_plugin.initialize_plugin(sim.get_engine())
    YamlDataLoader(str_data=STRUCTURES).load(sim.get_engine())

    # character_1 = sim.get_engine().create_character("Civilian")
    # character_2 = sim.get_engine().create_character("Civilian")
    #
    # sim.world.add_gameobject(character_1)
    # sim.world.add_gameobject(character_2)
    #
    # print("=== CHARACTERS ==")
    # print(character_1.get_component(GameCharacter))
    # print(character_2.get_component(GameCharacter))
    #
    # loc1 = sim.get_engine().create_place("Space Casino")
    # loc2 = sim.get_engine().create_place("Mars")
    # loc3 = sim.get_engine().create_place("Kamino")
    #
    # sim.world.add_gameobject(loc1)
    # sim.world.add_gameobject(loc2)
    # sim.world.add_gameobject(loc3)
    #
    # print("=== LOCATIONS ==")
    # print(loc1)
    # print(loc2)
    # print(loc3)

    for _ in range(100):
        sim.step()

    # print("=== RELATIONSHIPS ==")
    # print(behavior_utils.get_relationship_net(sim.world).get_connection(character_1.id, character_2.id))
    # print(behavior_utils.get_relationship_net(sim.world).get_connection(character_2.id, character_1.id))

    print("Done")


if __name__ == "__main__":
    main()
