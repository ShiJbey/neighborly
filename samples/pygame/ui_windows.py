from pprint import pformat

import pygame
import pygame_gui

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject
from neighborly.simulation import Simulation


class CharacterInfoWindow(pygame_gui.elements.UIWindow):
    """
    Wraps a pygame_ui panel to display information
    about a given character
    """

    def __init__(
        self, character: GameObject, sim: Simulation, ui_manager: pygame_gui.UIManager
    ) -> None:
        super().__init__(
            pygame.Rect((10, 10), (320, 240)),
            ui_manager,
            window_display_title=str(character.get_component(GameCharacter).name),
            object_id=f"{character.id}",
        )
        self.ui_manager = ui_manager
        self.text = pygame_gui.elements.UITextBox(
            f"{character.get_component(GameCharacter)}",
            pygame.Rect(0, 0, 320, 240),
            manager=ui_manager,
            container=self,
            parent_element=self,
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        handled = super().process_event(event)
        if (
            event.type == pygame.USEREVENT
            and event.type == pygame_gui.UI_BUTTON_PRESSED
            and event.ui_object_id == "#character_window.#title_bar"
            and event.ui_element == self.title_bar
        ):
            handled = True

            event_data = {
                "type": "character_window_selected",
                "ui_element": self,
                "ui_object_id": self.most_specific_combined_id,
            }

            window_selected_event = pygame.event.Event(pygame.USEREVENT, event_data)

            pygame.event.post(window_selected_event)

        return handled


class PlaceInfoWindow(pygame_gui.elements.UIWindow):
    """
    Wraps a pygame_ui panel to display information
    about a given character
    """

    def __init__(
        self, place: GameObject, sim: Simulation, ui_manager: pygame_gui.UIManager
    ) -> None:
        super().__init__(
            pygame.Rect((10, 10), (320, 240)),
            ui_manager,
            window_display_title=str(place.name),
            object_id=f"{place.id}",
        )
        self.ui_manager = ui_manager
        self.text = pygame_gui.elements.UITextBox(
            f"{place}",
            pygame.Rect(0, 0, 320, 240),
            manager=ui_manager,
            container=self,
            parent_element=self,
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        handled = super().process_event(event)
        if (
            event.type == pygame.USEREVENT
            and event.type == pygame_gui.UI_BUTTON_PRESSED
            and event.ui_object_id == "#character_window.#title_bar"
            and event.ui_element == self.title_bar
        ):
            handled = True

            event_data = {
                "type": "character_window_selected",
                "ui_element": self,
                "ui_object_id": self.most_specific_combined_id,
            }

            window_selected_event = pygame.event.Event(pygame.USEREVENT, event_data)

            pygame.event.post(window_selected_event)

        return handled


class GameObjectInfoWindow(pygame_gui.elements.UIWindow):
    def __init__(
        self,
        gameobject: GameObject,
        manager: pygame_gui.UIManager,
    ):
        super().__init__(
            rect=pygame.Rect(0, 0, 320, 240),
            manager=manager,
            window_display_title=str(gameobject),
            element_id=f"window_{gameobject.id}",
            resizable=True,
        )
        self.text = pygame_gui.elements.UITextBox(
            pformat(gameobject.to_dict()).replace("\n", "<br>"),
            relative_rect=pygame.Rect(0, 0, 320, 240),
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom",
            },
            manager=manager,
            container=self,
            parent_element=self,
        )
