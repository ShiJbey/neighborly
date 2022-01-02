from enum import IntEnum


class ActivityFlags(IntEnum):
    GAMBLING = (1 << 0)
    SHOPPING = (1 << 1)
    EATHING = (1 << 2)
    DRINKING = (1 << 3)
    STUDYING = (1 << 4)
    RECREATION = (1 << 5)
    SOCIALIZING = (1 << 6)


class Activity:
    """Something that characters may do at a location"""
