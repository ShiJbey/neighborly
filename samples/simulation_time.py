"""
samples/simulation_time.py

This is a small sample that show the 336-day year with 28-day months
"""
from neighborly import SimDateTime
from neighborly.core.time import DAYS_PER_YEAR

if __name__ == "__main__":
    date = SimDateTime(1, 1, 1)

    for _ in range(DAYS_PER_YEAR + 2):
        print(str(date))
        date.increment(days=1)
