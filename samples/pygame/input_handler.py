from collections import defaultdict
from typing import Callable, DefaultDict, Dict, List

import pygame


class InputHandler:
    """Manages handling input events for the game"""

    __slots__ = "callbacks", "key_callbacks"

    def __init__(self) -> None:
        self.callbacks: DefaultDict[
            int, List[Callable[[pygame.event.Event], None]]
        ] = defaultdict(list)
        self.key_callbacks: Dict[
            int, DefaultDict[int, List[Callable[[pygame.event.Event], None]]]
        ] = {pygame.KEYUP: defaultdict(list), pygame.KEYDOWN: defaultdict(list)}

    def emit(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYUP or event.type == pygame.KEYDOWN:
            for cb in self.key_callbacks[event.type][event.key]:
                cb(event)
            return
        for cb in self.callbacks[event.type]:
            cb(event)

    def on_key_up(
        self, key: int, callback: Callable[[pygame.event.Event], None]
    ) -> None:
        self.key_callbacks[pygame.KEYUP][key].append(callback)

    def on_key_down(
        self, key: int, callback: Callable[[pygame.event.Event], None]
    ) -> None:
        self.key_callbacks[pygame.KEYDOWN][key].append(callback)

    def on(self, event: int, callback: Callable[[pygame.event.Event], None]) -> None:
        self.callbacks[event].append(callback)
