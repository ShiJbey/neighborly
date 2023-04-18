"""Neighborly Commandline Interface.

"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any, Dict, Optional

import yaml

from neighborly import NeighborlyConfig
from neighborly.__version__ import VERSION
from neighborly.exporter import export_to_json
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
        help="Path to the configuration file to load before running",
    )

    parser.add_argument("-o", "--output", help="path to write final simulation state")

    parser.add_argument(
        "--no-emit",
        default=False,
        action="store_true",
        help="Disable creating an output file with the simulation's final state",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        default=False,
        action="store_true",
        help="Disable all printing to stdout",
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
            "relationship_schema": {
                "components": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "InteractionScore": {
                        "min_value": -5,
                        "max_value": 5,
                    },
                }
            },
            "time_increment": "1mo",
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

    if not args.no_emit:
        output_path = (
            args.output if args.output else f"neighborly_{sim.config.seed}.json"
        )

        with open(output_path, "w") as f:
            data = export_to_json(sim)
            f.write(data)
