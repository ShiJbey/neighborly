from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    a: int
    b: bool
    c: str


if __name__ == "__main__":

    # cd = {"a": 9, "b": False, "c": "Apples"}
    cd = {"a": 9, "b": False}

    conf = Config(**cd)

    print(conf)
