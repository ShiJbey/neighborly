"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from neighborly.components.settlement import District, Settlement
from neighborly.ecs import GameObject


def debug_print_gameobject(gameobject: GameObject) -> None:
    """Pretty prints a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to print.
    """

    component_debug_strings = "".join(
        [f"\t{repr(c)}\n" for c in gameobject.get_components()]
    )

    debug_str = (
        f"name: {gameobject.name}\n"
        f"uid: {gameobject.uid}\n"
        f"components: [\n{component_debug_strings}]"
    )

    print(debug_str)


def get_settlement_description(settlement: Settlement) -> str:
    """Create a string description of the settlement.

    Parameters
    ----------
    settlement
        The settlement to describe.

    Returns
    -------
    str
        The description.
    """
    districts = list(settlement.districts)

    concatenated_district_names = ", ".join([d.name for d in districts])

    description = (
        f"{settlement.name} has a population of {settlement.population}. "
        f"It has {len(districts)} districts ({concatenated_district_names})."
    )

    for district in districts:
        description += (
            f"{district.name} is {district.get_component(District).description}. "
        )

    return description
