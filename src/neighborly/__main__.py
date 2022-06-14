import argparse
import json
import logging
import os
import pathlib
import random
import sys
from typing import Any, Dict, Optional

import yaml

import neighborly
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.loaders import UnsupportedFileType
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig
from neighborly.server import NeighborlyServer

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
