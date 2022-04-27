from neighborly.core.character.character import CharacterDefinition, create_character
from neighborly.core.character.character import GenerationConfig, FamilyGenerationOptions, LifeCycleConfig, AgeRanges
from neighborly.simulation import Simulation, NeighborlyConfig

BASE_CHARACTER_TYPE = CharacterDefinition(
    name="BaseCharacter",
    lifecycle=LifeCycleConfig(
        can_age=True,
        can_die=True,
        chance_of_death=0.6,
        romantic_feelings_age=13,
        marriageable_age=18,
        age_ranges=AgeRanges(
            child=(0, 10),
            teen=(11, 19),
            young_adult=(20, 29),
            adult=(30, 60),
            senior=(60, 85),
        )
    ),
    generation=GenerationConfig(
        first_name="#first_name#",
        last_name="#last_name#",
        family=FamilyGenerationOptions(
            probability_spouse=0.5,
            probability_children=0.3,
            num_children=(0, 3)
        ),
    )
)


def main():
    CharacterDefinition.register_type(BASE_CHARACTER_TYPE)
    sim = Simulation.from_config(NeighborlyConfig())
    print(create_character(BASE_CHARACTER_TYPE,
                           sim.get_engine().get_rng(), age_range="child"))
    print(create_family(BASE_CHARACTER_TYPE, sim.get_engine().get_rng()))


if __name__ == "__main__":
    main()
