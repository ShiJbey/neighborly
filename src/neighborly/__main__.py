import argparse
import json
import logging
import os
import pathlib
import random
import sys
import importlib
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel

import neighborly
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.loaders import UnsupportedFileType
from neighborly.simulation import Simulation, PluginSetupError, Plugin
from neighborly.server import NeighborlyServer
import neighborly.core.utils.utilities as utilities

logger = logging.getLogger(__name__)

DEFAULT_NEIGHBORLY_CONFIG = NeighborlyConfig(
    simulation=SimulationConfig(
        seed=random.randint(0, 999999),
        hours_per_timestep=6,
        start_date="0000-00-00T00:00.000z",
        end_date="0001-00-00T00:00.000z",
        days_per_year=10,
    ),
    plugins=["neighborly.plugins.default_plugin", "neighborly.plugins.talktown"],
)


class SimulationConfig(BaseModel):
    """Configuration parameters for a Neighborly instance

    Attributes
    ----------
    seed: int
        The seed provided to the random number factory
    hours_per_timestep: int
        How many in-simulation hours elapse every simulation tic
    town: TownConfig
        Configuration settings for town creation
    """

    seed: int
    hours_per_timestep: int
    start_date: str
    end_date: str
    days_per_year: int


class PluginConfig(BaseModel):
    """
    Settings for loading and constructing a plugin

    Attributes
    ----------
    name: str
        Name of the plugin to load
    options: Dict[str, Any]
        Parameters to pass to the plugin when constructing
        and loading it
    """

    name: str
    path: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class NeighborlyConfig(BaseModel):
    """
    Static configuration setting for the Neighborly

    Attributes
    ----------
    simulation: SimulationConfig
        Static configuration settings specifically for
        the simulation instance
    plugins: List[Union[str, PluginConfig]]
        Names of plugins to load or names combined with
        instantiation parameters
    path: str
        Path to the config file
    """

    quiet: bool = False
    simulation: SimulationConfig
    plugins: List[Union[str, PluginConfig]] = Field(default_factory=list)
    path: str = "."

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**utilities.merge(data, defaults.dict()))


def add_plugin(self, plugin: Union[str, PluginConfig, Plugin]) -> Simulation:
    """Add plugin to simulation"""
    if isinstance(plugin, str):
        self._dynamic_load_plugin(plugin)
    elif isinstance(plugin, PluginConfig):
        self._dynamic_load_plugin(plugin.name, plugin.path, **plugin.options)
    else:
        plugin.setup(self)
        logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")
    return self


def _dynamic_load_plugin(
    self, module_name: str, path: Optional[str] = None, **kwargs
) -> None:
    """
    Load a plugin

    Parameters
    ----------
    module_name: str
        Name of module to load
    """
    path_prepended = False

    if path:
        path_prepended = True
        plugin_abs_path = os.path.abspath(path)
        sys.path.insert(0, plugin_abs_path)
        logger.debug(f"Temporarily added plugin path '{plugin_abs_path}' to sys.path")

    try:
        plugin_module = importlib.import_module(module_name)
        plugin: Plugin = plugin_module.__dict__["get_plugin"]()
        plugin.setup(self, **kwargs)
        logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")
    except KeyError:
        raise PluginSetupError(
            f"'get_plugin' function not found for plugin: {module_name}"
        )
    finally:
        # Remove the given plugin path from the front
        # of the system path to prevent module resolution bugs
        if path_prepended:
            sys.path.pop(0)


def load_config_from_path(config_path: str) -> Dict[str, Any]:
    """
    This function loads the configuration file at the given path

    Parameters
    ----------
    config_path: str
        Path to a configuration file to load
    """
    path = pathlib.Path(os.path.abspath(config_path))

    with open(path, "r") as f:
        if path.suffix.lower() == ".json":
            return json.load(f)
        elif path.suffix.lower() == ".yaml":
            return yaml.safe_load(f)
        else:
            logging.error(
                f"Attempted to load config from incorrect file type: {path.suffix}."
            )
            raise UnsupportedFileType(path.suffix)


def try_load_local_config() -> Optional[Dict[str, Any]]:
    """
    Attempt to load a configuration file in the current working
    directory.
    """
    config_load_precedence = [
        os.path.join(os.getcwd(), "neighborlyconfig.yaml"),
        os.path.join(os.getcwd(), "neighborlyconfig.yml"),
        os.path.join(os.getcwd(), "neighborlyconfig.json"),
    ]

    for path in config_load_precedence:
        if os.path.exists(path):
            return load_config_from_path(path)

    return None


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Run Neighborly social simulation")
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="Print the version of Neighborly",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to the neighborlyconfig.yaml file to load for configuration",
    )
    parser.add_argument("-o", "--output", help="path to write final simulation state")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="Print verbose debug output and save a log file",
    )
    parser.add_argument(
        "--no-emit",
        default=False,
        action="store_true",
        help="Disable creating an output file with the simulation's final state",
    )
    parser.add_argument(
        "-q,",
        "--quiet",
        default=False,
        action="store_true",
        help="Disable all printing to stdout",
    )
    parser.add_argument(
        "--server", default=False, action="store_true", help="Run web server UI"
    )
    return parser


def main():
    args = get_arg_parser().parse_args()

    if args.version:
        print(neighborly.__version__)
        sys.exit(0)

    if args.debug:
        logging.basicConfig(
            filename="neighborly.log", filemode="w", level=logging.DEBUG
        )

    config = DEFAULT_NEIGHBORLY_CONFIG
    if args.config:
        config = NeighborlyConfig.from_partial(
            load_config_from_path(args.config), config
        )
        config.path = os.path.abspath(args.config)
    else:
        loaded_settings = try_load_local_config()
        if loaded_settings:
            logger.debug("Successfully loaded config from cwd.")
            config = NeighborlyConfig.from_partial(loaded_settings, config)

    config.quiet = args.quiet

    sim = Simulation(config)

    if args.server:
        server = NeighborlyServer(sim)
        server.run()
    else:
        sim.establish_setting()

        if not args.no_emit:
            output_path = (
                args.output
                if args.output
                else f"{sim.config.simulation.seed}_{sim.get_town().name.replace(' ', '_')}.json"
            )

            with open(output_path, "w") as f:
                data = NeighborlyJsonExporter().export(sim.world)
                f.write(data)
                logger.debug(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()


# Load Plugins
# for plugin in config.plugins:
#     if isinstance(plugin, str):
#         self._load_plugin(plugin)
#     else:
#         plugin_path = os.path.join(
#             pathlib.Path(config.path).parent, plugin.path if plugin.path else ""
#         )
#         self._load_plugin(plugin.name, plugin_path, **plugin.options)
