import os
import pathlib
import logging

from neighborly.simulation import PluginContext
from neighborly.loaders import YamlDataLoader
from neighborly.core.ecs import World
from neighborly.core.town import Town
from neighborly.core.engine import NeighborlyEngine

logger = logging.getLogger(__name__)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent


def establish_town(world: World, **kwargs) -> None:
    """
    Adds an initial set of families and businesses
    to the start of the town.

    This system runs once, then removes itself from
    the ECS to free resources.

    Parameters
    ----------
    world : World
        The world instance of the simulation

    Notes
    -----
    This function is based on the original Simulation.establish_setting
    method in talktown.
    """
    logger.debug("Establishing town")

    engine = world.get_resource(NeighborlyEngine)
    town = world.get_resource(Town)

    vacant_lots = town.layout.get_vacancies()
    # Each family requires 2 lots (1 for a house, 1 for a business)
    # Save two lots for either a coalmine, quarry, or farm
    n_families_to_add = (len(vacant_lots) // 2) - 1

    for _ in range(n_families_to_add - 1):
        # create residents
        # create Farm
        farm = engine.create_business("Farm")
        # trigger hiring event
        # trigger home move event

    random_num = engine.get_rng().random()
    if random_num < 0.2:
        # Create a Coalmine 20% of the time
        coalmine = engine.create_business("Coal Mine")
    elif 0.2 <= random_num < 0.35:
        # Create a Quarry 15% of the time
        quarry = engine.create_business("Quarry")
    else:
        # Create Farm 65% of the time
        farm = engine.create_business("Farm")

    world.remove_system(establish_town)

    logger.debug("Town established. 'establish_town' function removed from systems")


def setup(ctx: PluginContext, **kwargs) -> None:
    """Entry point for the plugin"""
    logger.debug("Loading neighborly_talktown plugin")

    YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(ctx.engine)

    ctx.world.add_system(establish_town)

    logger.debug("Neighborly_talktown plugin loaded successfully")
