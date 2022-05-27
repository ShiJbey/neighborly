import random
from typing import Optional, Generator
from neighborly.core.time import SimDateTime, TimeDelta, DAYS_PER_YEAR


def lod_generator(
    current_date: SimDateTime,
    high_lod_step: int,
    days_per_year: int,
    end_date: Optional[SimDateTime] = None,
) -> Generator[int, None, None]:
    """
    Yields time step increments based on the current date,
    switching between low and high levels-of-detail.
    """
    while True:
        one_year_ahead = current_date.to_ordinal() + DAYS_PER_YEAR

        # Sample the fully simulated days for the next year
        high_res_days = set(
            random.sample(
                range(current_date.to_ordinal(), one_year_ahead),
                days_per_year,
            )
        )

        while current_date.to_ordinal() < one_year_ahead:
            if current_date.to_ordinal() in high_res_days:
                current_date += TimeDelta(hours=high_lod_step)
                yield high_lod_step
            else:
                current_date += TimeDelta(hours=24)
                yield 24

            if end_date and current_date > end_date:
                return


class SimpleSim:
    def __init__(self) -> None:
        self.x: int = 0
        self.y: int = 0
        self.z: int = 0

    def __repr__(self) -> str:
        return f"{self.x=} {self.y=} {self.z=}"

    def step(self) -> Generator[None, None, None]:
        while True:
            self.x += 1
            self.y += 3
            self.z -= 2
            yield


if __name__ == "__main__":

    # current_date = SimDateTime()
    # end_date = SimDateTime(year=1)

    # for delta_time in lod_generator(current_date, 6, 10, end_date):
    #     print(current_date.to_date_str())

    sim = SimpleSim()

    for _ in sim.step():
        print(sim)
