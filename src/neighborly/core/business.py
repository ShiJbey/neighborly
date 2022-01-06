from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessConfig:
    business_type: str


@dataclass
class Business:
    config: BusinessConfig
