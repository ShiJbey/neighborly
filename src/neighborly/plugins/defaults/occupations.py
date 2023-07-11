from __future__ import annotations

from neighborly.components.business import Occupation


class Librarian(Occupation):
    social_status = 2


class Owner(Occupation):
    social_status = 4


class Barista(Occupation):
    social_status = 2
