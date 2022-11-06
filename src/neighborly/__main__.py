from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import pathlib
import random
import sys
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field

import neighborly
import neighborly.core.utils.utilities as utilities
from neighborly import SimDateTime
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.simulation import Plugin, PluginSetupError, SimulationBuilder

logger = logging.getLogger(__name__)


class PluginConfig(BaseModel):
    """
    Settings for loading and constructing a plugin

    Fields
    ----------
    name: str
        Name of the plugin to load
    path: Optional[str]
        The path where the plugin is located
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

    Fields
    ----------
    quiet: bool
        Should the simulation not print to the console
    seed: int
        Seed used for random number generation
    hours_per_timestep: str
        How many hours elapse each simulation step
    world_gen_start: str
        Date when world generation starts (YYYY-MM-DD)
    world_gen_end: str
        Date when world generation ends (YYYY-MM-DD)
    town_name: str
        Name to give the generated town
    town_size: Literal["small", "medium", "large"]
        The size of th town to create
    plugins: List[Union[str, PluginConfig]]
        Names of plugins to load or names combined with
        instantiation parameters
    path: str
        Path to the config file
    """

    quiet: bool = False
    seed: Union[int, str]
    hours_per_timestep: int
    world_gen_start: str
    world_gen_end: str
    town_name: str
    town_size: Literal["small", "medium", "large"]
    plugins: List[Union[str, PluginConfig]] = Field(default_factory=list)
    path: str = "."

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**utilities.merge(data, defaults.dict()))


def load_plugin(module_name: str, path: Optional[str] = None) -> Plugin:
    """
    Load a plugin

    Parameters
    ----------
    module_name: str
        Name of module to load
    path: Optional[str]
        Path where the Python module lives
    """
    path_prepended = False

    if path:
        path_prepended = True
        plugin_abs_path = os.path.abspath(path)
        sys.path.insert(0, plugin_abs_path)
        logger.debug(f"Temporarily added plugin path '{plugin_abs_path}' to sys.path")

    try:
        plugin_module = importlib.import_module(module_name)
        plugin: Plugin = getattr(plugin_module, "get_plugin")()
        return plugin
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
            raise ValueError(
                f"Attempted to load config from incorrect file type: {path.suffix}."
            )


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

    config: NeighborlyConfig = NeighborlyConfig(
        seed=random.randint(0, 999999),
        hours_per_timestep=6,
        world_gen_start="1839-08-19T00:00.000z",
        world_gen_end="1979-08-19T00:00.000z",
        town_size="medium",
        town_name="#town_name#",
        plugins=["neighborly.plugins.default_plugin", "neighborly.plugins.talktown"],
    )

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

    sim_builder = SimulationBuilder(
        seed=config.seed,
        starting_date=config.world_gen_start,
        time_increment_hours=config.hours_per_timestep,
        print_events=not args.quiet,
    )

    for plugin_entry in config.plugins:
        if isinstance(plugin_entry, str):
            plugin = load_plugin(plugin_entry)
            sim_builder.add_plugin(plugin)
        else:
            plugin = load_plugin(plugin_entry.name, plugin_entry.path)
            sim_builder.add_plugin(plugin, **plugin_entry.options)

    sim = sim_builder.build()

    sim.run_until(SimDateTime.from_str(config.world_gen_end))

    if not args.no_emit:
        output_path = (
            args.output
            if args.output
            else f"{sim.seed}_{sim.town.name.replace(' ', '_')}.json"
        )

        with open(output_path, "w") as f:
            data = NeighborlyJsonExporter().export(sim)
            f.write(data)
            logger.debug(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()
