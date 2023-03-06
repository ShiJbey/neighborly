from typing import Any, List

import pytest

from neighborly import Neighborly
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.systems import System


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

    def run(self, *args: Any, **kwargs: Any) -> None:
        self.elapsed_times.append(self.elapsed_time.total_hours)
        self.run_times.append(self.world.get_resource(SimDateTime).copy())


@pytest.fixture()
def test_sim() -> Neighborly:
    sim = Neighborly()
    return sim


def test_elapsed_time(test_sim: Neighborly):
    elapsed_times = []
    test_sim.add_system(TestSystem(TimeDelta(), elapsed_times, []))
    test_sim.step()
    test_sim.step()
    test_sim.step()
    assert elapsed_times == [0, 4, 4]


def test_interval_run(test_sim: Neighborly):
    run_times = []
    test_sim.add_system(TestSystem(TimeDelta(hours=6), [], run_times))
    test_sim.step()
    test_sim.step()
    test_sim.step()
    test_sim.step()
    test_sim.step()
    test_sim.step()
    assert run_times == [
        SimDateTime(1, 1, 1, 0),
        SimDateTime(1, 1, 1, 8),
        SimDateTime(1, 1, 1, 16),
    ]
