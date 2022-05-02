import argparse
import json
import logging
import os
import random
import pathlib
from typing import Any, Dict, Optional

import yaml

from neighborly.exporter import NeighborlyJsonExporter
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig
from neighborly.loaders import UnsupportedFileType

logger = logging.getLogger(__name__)

DEFAULT_NEIGHBORLY_CONFIG = NeighborlyConfig(
    simulation=SimulationConfig(
        seed=random.randint(0, 999999),
        hours_per_timestep=6,
        start_date="0000-00-00T00:00.000z",
        end_date="0100-00-00T00:00.000z",
    ),
    plugins=["neighborly.plugins.default_plugin"],
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
    parser.add_argument("-o", "--output", help="path to write output file")
    parser.add_argument(
        "--no-emit",
        default=False,
        action="store_true",
        help="Disable creating an output file",
    )
    parser.add_argument(
        "--config", help="Load a simulation config from the following path"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="neighborly.log",
        help="File to save logging output to",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    return parser


def main():
    args = get_arg_parser().parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    if args.log_file:
        logging.basicConfig(filename=args.log_file, filemode="w", level=log_level)
    else:
        logging.basicConfig(level=log_level)

    config = DEFAULT_NEIGHBORLY_CONFIG
    if args.config:
        config = NeighborlyConfig.from_partial(
            load_config_from_path(args.config), config
        )
    else:
        loaded_settings = try_load_local_config()
        if loaded_settings:
            logger.debug("Successfully loaded config from cwd.")
            config = NeighborlyConfig.from_partial(loaded_settings, config)

    sim = Simulation(config)

    sim.run()

    if not args.no_emit:
        output_path = (
            args.output
            if args.output
            else f"{sim.config.simulation.seed}_{sim.get_town().name.replace(' ', '_')}.json"
        )

        with open(output_path, "w") as f:
            data = NeighborlyJsonExporter().export(sim.world)
            f.write(data)
            print(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()
