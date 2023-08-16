"""Neighborly Commandline Interface.

"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import Any, Dict, Optional

import yaml

from neighborly.__version__ import VERSION
from neighborly.config import NeighborlyConfig
from neighborly.exporter import export_to_json
from neighborly.settlement import Settlement
from neighborly.simulation import Neighborly


def get_args() -> argparse.Namespace:
    """Configure CLI argument parser and parse args.

    Returns
    -------
    argparse.Namespace
        parsed CLI arguments.
    """

    parser = argparse.ArgumentParser("The Neighborly commandline interface")

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
        help="Path to the configuration file",
    )

    parser.add_argument(
        "-o", "--output", help="Specify path to write generated world data"
    )

    parser.add_argument(
        "--no-output",
        default=False,
        action="store_true",
        help="Do not output generated world data",
    )

    return parser.parse_args()


def load_config_from_path(config_path: str) -> Dict[str, Any]:
    """This function loads the configuration file at the given path.

    Parameters
    ----------
    config_path
        Path to a configuration file to load.

    Returns
    -------
    Dict[str, Any]
        Configuration settings.
    """
    path = pathlib.Path(os.path.abspath(config_path))

    if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
        raise TypeError(
            f"Incorrect file type. Expected .yaml or .json but was {path.suffix}."
        )

    with open(path, "r") as f:
        return yaml.safe_load(f)


def try_load_local_config() -> Optional[Dict[str, Any]]:
    """Attempt to load a configuration file in the current working directory.

    Returns
    -------
    Dict[str, Any] or None
        Configuration settings.
    """

    config_load_precedence = [
        os.path.join(os.getcwd(), "neighborly.config.yaml"),
        os.path.join(os.getcwd(), "neighborly.config.yml"),
        os.path.join(os.getcwd(), "neighborly.config.json"),
    ]

    for path in config_load_precedence:
        if os.path.exists(path):
            return load_config_from_path(path)

    return None


def run():
    """Run the commandline interface."""

    args = get_args()

    if args.version:
        print(VERSION)
        sys.exit(0)

    config = NeighborlyConfig.parse_obj(
        {
            "plugins": [
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown",
            ],
        }
    )

    if args.config:
        config = NeighborlyConfig.from_partial(
            load_config_from_path(args.config), config
        )
    else:
        loaded_settings = try_load_local_config()
        if loaded_settings:
            config = NeighborlyConfig.from_partial(loaded_settings, config)

    sim = Neighborly(config)

    sim.run_for(config.years_to_simulate)

    settlement_name = sim.world.resource_manager.get_resource(Settlement).name

    if args.no_output is False:
        output_path = (
            args.output if args.output else f"{settlement_name}_{sim.config.seed}.json"
        )

        with open(output_path, "w") as f:
            data = export_to_json(sim)
            f.write(data)
