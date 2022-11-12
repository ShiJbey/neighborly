from typing import List

import pytest

from neighborly import SimDateTime, Simulation, World
from neighborly.builtin.systems import LinearTimeSystem
from neighborly.core.system import System
from neighborly.core.time import TimeDelta


class TestSystem(System):
    def __init__(
        self,
        interval: TimeDelta,
        elapsed_times: List[int],
        run_times: List[SimDateTime],
    ) -> None:
        super().__init__(interval)
        self.elapsed_times: List[int] = elapsed_times
        self.run_times: List[SimDateTime] = run_times

    def run(self, *args, **kwargs) -> None:
        self.elapsed_times.append(self.elapsed_time.total_hours)
        self.run_times.append(self.world.get_resource(SimDateTime).copy())


@pytest.fixture()
def test_world() -> World:
    world = World()
    world.add_resource(SimDateTime())
    world.add_system(LinearTimeSystem(increment=TimeDelta(hours=4)))
    return world


def test_elapsed_time(test_world):
    elapsed_times = []
    test_world.add_system(TestSystem(TimeDelta(), elapsed_times, []))
    test_world.step()
    test_world.step()
    test_world.step()
    assert elapsed_times == [0, 4, 4]


def test_interval_run(test_world):
    run_times = []
    test_world.add_system(TestSystem(TimeDelta(hours=6), [], run_times))
    test_world.step()
    test_world.step()
    test_world.step()
    test_world.step()
    test_world.step()
    test_world.step()
    assert run_times == [
        SimDateTime(hour=8),
        SimDateTime(hour=16),
        SimDateTime(day=1, hour=0),
    ]
