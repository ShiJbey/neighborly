import argparse
import importlib
import importlib.util
import logging
import sys
from typing import Optional

from neighborly.exporter import NeighborlyJsonExporter
from neighborly.simulation import NeighborlyConfig, Simulation

logger = logging.getLogger(__name__)


def load_config(path: Optional[str]) -> NeighborlyConfig:
    """Try to load configuration from current directory"""
    config_path = path if path else "neighborlyconfig.py"

    try:
        spec = importlib.util.spec_from_file_location("neighborlyconfig", config_path)
        if spec and spec.loader:
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            return config_module.CONFIG  # type: ignore
        else:
            logger.error(f"Could not find config at path: '{path}'")
            return NeighborlyConfig()
    except FileNotFoundError:
        if path:
            logger.error(f"Could not find config at path: '{path}'")
            sys.exit(1)
        else:
            return NeighborlyConfig()
    except ModuleNotFoundError:
        logger.error(f"Could not find config at path: '{path}'")
        return NeighborlyConfig()


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Run Neighborly social simulation")
    parser.add_argument(
        "-o", "--output",
        help="path to write output file")
    parser.add_argument(
        "--no-emit",
        default=False,
        action='store_true',
        help="Disable creating an output file")
    parser.add_argument(
        "--config",
        help="Load a simulation config from the following path")
    parser.add_argument(
        "--log-file",
        type=str,
        default="neighborly.log",
        help="Enable logging ",
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        default=False,
        help="Enable logging",
    )
    return parser


def main():
    args = get_arg_parser().parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    if args.log_file:
        logging.basicConfig(filename=args.log_file, filemode='w', level=log_level)
    else:
        logging.basicConfig(level=log_level)

    if args.debug:
        logging.debug("Neighborly debug output enabled.")

    config = load_config(args.config)

    sim = Simulation.from_config(config)

    sim.run()

    if not args.no_emit:
        output_path = args.output if args.output else f"{sim.config.seed}_{sim.get_town().name.replace(' ', '_')}.json"

        with open(output_path, 'w') as f:
            data = NeighborlyJsonExporter().export(sim.world)
            f.write(data)
            print(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()
