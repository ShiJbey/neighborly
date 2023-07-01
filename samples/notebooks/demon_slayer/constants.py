"""Neighborly Demon Slayer Constants.

This module contains definitions for constant values used during the simulation.

"""

# ELO parameters used to update power levels
ELO_SCALE: int = 255
ELO_K: int = 16

# Maximum power level for a demon or demon slayer
POWER_LEVEL_MAX: int = 255

# Minimum power levels for each demon slayer rank
MIZUNOTO_PL: int = 0
MIZUNOE_PL: int = 15
KANOTO_PL: int = 30
KANOE_PL: int = 50
TSUCHINOTO_PL: int = 65
TSUCHINOE_PL: int = 80
HINOTO_PL: int = 100
HINOE_PL: int = 120
KINOTO_PL: int = 140
KINOE_PL: int = 160
HASHIRA_PL: int = 220

# Minimum power levels for each demon rank
LOWER_DEMON_PL: int = 0
DEMON_PL: int = 40
BLOOD_DEMON_PL: int = 80
HIGHER_DEMON_PL: int = 120
SUPERIOR_DEMON_PL: int = 160
LOWER_MOON_PL: int = 200
UPPER_MOON_PL: int = 220
