from neighborly.core.engine import NeighborlyEngine
from neighborly.core.authoring.factories import BusinessFactory


def main():
    engine = NeighborlyEngine()
    engine.register_factory("business", BusinessFactory())


if __name__ == "__main__":
    main()
