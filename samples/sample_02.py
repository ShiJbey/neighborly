import random
from typing import Dict

import numpy as np
import numpy.typing as npt

import neighborly.core.character.values as values


def prototype_similarity():

    def similarity(a, b):
        cos_sim: float = np.dot(a, b) / (
            np.linalg.norm(a) * np.linalg.norm(b))

        final_val: int = round(cos_sim * 50)

        return cos_sim, final_val

    a = np.array([1, 0], dtype=np.int8)
    b = np.array([0, 1], dtype=np.int8)
    c = np.array([1, 1], dtype=np.int8)
    d = np.array([-1, -1], dtype=np.int8)

    print(similarity(a, b))  # should be 0
    print(similarity(c, d))  # should be -1
    print(similarity(a, a))  # should be 1
    print(similarity(a, c))  # should be between 0 and 1


def prototpye_character_value_gen():
    # Select 6 Traits
    traits = [str(trait.value)
              for trait in random.sample(list(values.ValueTrait), 6)]
    trait_set = set(traits)

    # select 3 of the 6 to like and leave the rest as dislikes
    high_values = random.sample(traits, 3)
    [trait_set.remove(trait) for trait in high_values]
    low_values = list(trait_set)

    # Generate values for each ([30,50] for high values, [-50,-30] for dislikes)
    values_overrides: Dict[str, int] = {}

    for trait in high_values:
        values_overrides[trait] = random.randint(30, 50)

    for trait in low_values:
        values_overrides[trait] = random.randint(-50, -30)

    character_values = values.CharacterValues(values_overrides)

    print(character_values.__repr__())


def main():
    # prototype_similarity()
    prototpye_character_value_gen()

    return


if __name__ == "__main__":
    main()
