import random
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Sequence,
    Tuple,
    Union,
    cast,
)

import pygame
import pygame_gui

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject
from neighborly.core.position import Position2D
from neighborly.core.town import LandGrid
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.plugins.talktown import TalkOfTheTownPlugin
from neighborly.simulation import Simulation, SimulationBuilder

# COMMON COLORS
SKY_BLUE = (153, 218, 232)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (99, 133, 108)
COLOR_BLUE = (0, 0, 255)
CHARACTER_COLOR = (66, 242, 245)
BUILDING_COLOR = (194, 194, 151)
BACKGROUND_COLOR = (232, 232, 213)
LOT_COLOR = (79, 107, 87)
GROUND_COLOR = (127, 130, 128)

# Number of pixels between lots
LOT_SIZE = 64
LOT_PADDING = 8


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


@dataclass
class GameConfig:
    width: int = 900
    height: int = 500
    fps: int = 60
    show_debug: bool = False


class BoxSprite(pygame.sprite.Sprite):
    """Draws a colored box to the screen"""

    def __init__(
        self,
        color: Tuple[int, int, int],
        width: int,
        height: int,
        x: int = 0,
        y: int = 0,
    ) -> None:
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.position = pygame.Vector2(x, y)
        self.rect.topleft = (round(self.position.x), round(self.position.y))


class PlaceSprite(pygame.sprite.Sprite):
    """Sprite used to represent a place in the town"""

    def __init__(
        self,
        place: GameObject,
        color: Tuple[int, int, int] = BUILDING_COLOR,
    ) -> None:
        super().__init__()
        self.place = place
        self.image = pygame.Surface([LOT_SIZE, LOT_SIZE])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        pos = place.get_component(Position2D)
        self.position = pygame.Vector2(
            LOT_PADDING + pos.x * (LOT_SIZE + LOT_PADDING),
            LOT_PADDING + pos.y * (LOT_SIZE + LOT_PADDING),
        )

        self.rect.topleft = (round(self.position.x), round(self.position.y))


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(
        self,
        surface: pygame.Surface,
        *sprites: Union[pygame.sprite.Sprite, Sequence[pygame.sprite.Sprite]],
    ) -> None:
        super().__init__(*sprites)
        self.surface = surface
        self.half_width = self.surface.get_width() // 2
        self.half_height = self.surface.get_height() // 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, camera_focus: pygame.math.Vector2) -> None:
        self.offset.x = camera_focus.x - self.half_width
        self.offset.y = camera_focus.y - self.half_height

        for sprite in self.sprites():
            if sprite.rect and sprite.image:
                offset_pos = pygame.math.Vector2(sprite.rect.topleft) - self.offset
                self.surface.blit(sprite.image, offset_pos)


class PlacesSpriteGroup(pygame.sprite.Group):
    def __init__(
        self,
        surface: pygame.Surface,
        *sprites: Union[PlaceSprite, Sequence[PlaceSprite]],
    ) -> None:
        super().__init__(*sprites)
        self.surface = surface
        self.half_width = self.surface.get_width() // 2
        self.half_height = self.surface.get_height() // 2
        self.offset = pygame.math.Vector2()
        self.sprite_dict: Dict[int, PlaceSprite] = {}

    def get_places(self) -> List[PlaceSprite]:
        return cast(List[PlaceSprite], self.sprites())

    def add(
        self,
        *sprites: Union[
            PlaceSprite,
            "PlacesSpriteGroup",
            Iterable[Union[PlaceSprite, "PlacesSpriteGroup"]],
        ],
    ) -> None:
        super(PlacesSpriteGroup, self).add(*sprites)
        for sprite in sprites:
            self.sprite_dict[sprite.place.id] = sprite

    def remove(self, *sprites: PlaceSprite) -> None:
        super().remove(*sprites)
        for sprite in sprites:
            del self.sprite_dict[sprite.place.id]

    def custom_draw(self, camera_focus: pygame.math.Vector2) -> None:
        self.offset.x = camera_focus.x - self.half_width
        self.offset.y = camera_focus.y - self.half_height

        for sprite in self.sprites():
            if sprite.rect and sprite.image:
                offset_pos = pygame.math.Vector2(sprite.rect.topleft) - self.offset
                self.surface.blit(sprite.image, offset_pos)


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


class Scene(ABC):
    """Scenes manage the visuals and controls for the current state of the game"""

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """
        Update the scene

        Parameters
        ----------
        delta_time: float
            The number of seconds that have elapsed since the last update
        """
        raise NotImplementedError

    @abstractmethod
    def draw(self) -> None:
        """Draw the scene to the display"""
        raise NotImplementedError

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle PyGame event"""
        raise NotImplementedError


class Camera:
    """
    Manages the offset for drawing the game world to the window.
    """

    __slots__ = "position", "speed"

    def __init__(self, position: pygame.math.Vector2 = None) -> None:
        self.position: pygame.math.Vector2 = (
            position if position else pygame.math.Vector2()
        )


class CameraController:
    """Manages the state of buttons pressed"""

    __slots__ = (
        "up",
        "right",
        "down",
        "left",
        "camera",
        "speed",
    )

    def __init__(self, camera: Camera, speed: int = 300) -> None:
        self.up: bool = False
        self.right: bool = False
        self.down: bool = False
        self.left: bool = False
        self.camera: Camera = camera
        self.speed: int = speed

    def move_up(self, value: bool) -> None:
        self.up = value

    def move_right(self, value: bool) -> None:
        self.right = value

    def move_down(self, value: bool) -> None:
        self.down = value

    def move_left(self, value: bool) -> None:
        self.left = value

    def update(self, delta_time: float) -> None:
        if self.up:
            self.camera.position += pygame.Vector2(0, -1) * delta_time * self.speed
        if self.left:
            self.camera.position += pygame.Vector2(-1, 0) * delta_time * self.speed
        if self.down:
            self.camera.position += pygame.Vector2(0, 1) * delta_time * self.speed
        if self.right:
            self.camera.position += pygame.Vector2(1, 0) * delta_time * self.speed

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(up={}, right={}, down={}, left={})".format(
            self.__class__.__name__, self.up, self.right, self.down, self.left
        )


class SimulationStatus(Enum):
    STOPPED = 0
    STEPPING = 1
    RUNNING = 2


class GameScene(Scene):
    """
    Main Scene for the game that shows the town changing over time.
    The player can pause, play, and step through time. In this mode
    players can inspect the state of the town, its buildings, and
    townspeople.

    Attributes
    ----------
    display: pygame.Surface
    """

    __slots__ = (
        "display",
        "background",
        "ui_manager",
        "camera",
        "sim",
        "sim_status",
        "input_handler",
    )

    def __init__(
        self,
        display: pygame.Surface,
        ui_manager: pygame_gui.UIManager,
        config: GameConfig,
    ) -> None:
        self.display: pygame.Surface = display
        self.background: pygame.Surface = pygame.Surface((config.width, config.height))
        self.background.fill(BACKGROUND_COLOR)
        self.ui_manager: pygame_gui.UIManager = ui_manager
        self.places_group: PlacesSpriteGroup = PlacesSpriteGroup(display)
        self.background_group: YSortCameraGroup = YSortCameraGroup(display)
        self.camera: Camera = Camera()
        self.camera_controller: CameraController = CameraController(self.camera)
        self.input_handler: InputHandler = InputHandler()

        self.sim: Simulation = self._init_sim()
        self.sim_status: SimulationStatus = SimulationStatus.STOPPED

        self._create_background(
            self.background_group, self.sim.world.get_resource(LandGrid).grid.shape
        )

        self.ui_elements = {
            "step-btn": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (100, 50)),
                text="Step",
                manager=self.ui_manager,
            ),
            "play-btn": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((100, 0), (100, 50)),
                text="Play",
                manager=self.ui_manager,
            ),
            "pause-btn": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((200, 0), (100, 50)),
                text="Pause",
                manager=self.ui_manager,
            ),
        }

        info_panel_rect = pygame.Rect((0, 0), (self.display.get_width(), 50))
        info_panel_rect.bottomleft = (-self.display.get_width(), 0)
        self.info_panel = pygame_gui.elements.UIPanel(
            relative_rect=info_panel_rect,
            manager=self.ui_manager,
            starting_layer_height=1,
            anchors={
                "left": "right",
                "right": "right",
                "top": "bottom",
                "bottom": "bottom",
            },
        )
        self.info_panel_text = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (self.display.get_width(), 50)),
            text=f"Town: {self.sim.town.name}, Date: {self.sim.time.to_date_str()}",
            manager=self.ui_manager,
            container=self.info_panel,
            parent_element=self.info_panel,
        )

        self._setup_input_handlers()

    @staticmethod
    def _init_sim() -> Simulation:

        sim = (
            SimulationBuilder(seed=random.randint(0, 999999))
            .add_plugin(DefaultPlugin())
            .add_plugin(TalkOfTheTownPlugin())
            .build()
        )

        return sim

    @staticmethod
    def _create_background(
        sprite_group: pygame.sprite.Group, town_size: Tuple[int, int]
    ) -> None:
        ground = BoxSprite(
            GROUND_COLOR,
            town_size[0] * LOT_SIZE + LOT_PADDING * (town_size[0] + 1),
            town_size[1] * LOT_SIZE + LOT_PADDING * (town_size[1] + 1),
        )
        sprite_group.add(ground)

        for row in range(town_size[1]):
            y_offset = LOT_PADDING + row * (LOT_SIZE + LOT_PADDING)
            for col in range(town_size[0]):
                x_offset = LOT_PADDING + col * (LOT_SIZE + LOT_PADDING)
                lot_sprite = BoxSprite(
                    LOT_COLOR,
                    LOT_SIZE,
                    LOT_SIZE,
                    x_offset,
                    y_offset,
                )
                sprite_group.add(lot_sprite)

    def draw(self) -> None:
        """Draw to the screen while active"""
        self.display.blit(self.background, (0, 0))
        self.background_group.custom_draw(self.camera.position)
        self.places_group.custom_draw(self.camera.position)

    def update(self, delta_time: float) -> None:
        """Update the state of the scene"""

        # Update the camera position
        self.camera_controller.update(delta_time)

        # Update the sprites (also remove sprites for deleted entities)
        self.places_group.update(delta_time=delta_time)

        # Update the UI
        self.info_panel_text.set_text(
            f"Town: {self.sim.town.name}, Date: {self.sim.time.to_date_str()}"
        )

        # Only update the simulation when the simulation is running
        # and the characters are no longer moving
        if self.sim_status == SimulationStatus.RUNNING:
            self._step_simulation()
        #
        #     # TODO: Add a procedure for adding place and character sprites.
        #     #       For now, just take the set difference between the groups
        #     #       and the state of the ECS. Then create new sprites with those.
        #
        #     existing_characters: Set[int] = set(
        #         map(lambda res: res[0], self.sim.world.get_component(GameCharacter))
        #     )
        #
        #     entities_with_sprites: Set[int] = set(
        #         map(
        #             lambda sprite: sprite.character.id,
        #             self.character_group.get_characters(),
        #         )
        #     )
        #
        #     new_character_entities = existing_characters - entities_with_sprites
        #
        #     for entity in new_character_entities:
        #         self.character_group.add(
        #             CharacterSprite(self.sim.world.get_gameobject(entity))
        #         )
        #
        #     existing_places: Set[int] = set(
        #         map(lambda res: res[0], self.sim.world.get_component(Location))
        #     )
        #
        #     places_with_sprites: Set[int] = set(
        #         map(lambda sprite: sprite.place.id, self.places_group.get_places())
        #     )
        #
        #     new_place_entities = existing_places - places_with_sprites
        #
        #     for entity in new_place_entities:
        #         self.places_group.add(
        #             PlaceSprite(self.sim.world.get_gameobject(entity))
        #         )
        #
        #     for character_sprite in self.character_group.get_characters():
        #         loc_id = character_sprite.character.get_component(
        #             GameCharacter
        #         ).location
        #         if loc_id in self.places_group.sprite_dict:
        #             loc = self.places_group.sprite_dict[loc_id]
        #
        #             if (
        #                 character_sprite.previous_destination
        #                 and character_sprite.previous_destination[0]
        #                 in self.places_group.sprite_dict
        #             ):
        #                 previous_loc = self.places_group.sprite_dict[
        #                     character_sprite.previous_destination[0]
        #                 ]
        #                 previous_loc.free_space(
        #                     character_sprite.previous_destination[1]
        #                 )
        #
        #             destination_space, destination_pos = loc.get_available_space()
        #             character_sprite.destination = (
        #                 loc_id,
        #                 destination_space,
        #                 destination_pos,
        #             )

    def _setup_input_handlers(self) -> None:
        self.input_handler.on(pygame_gui.UI_BUTTON_PRESSED, self._handle_button_click)
        self.input_handler.on(pygame.MOUSEBUTTONUP, self._handle_mouse_click)
        self.input_handler.on_key_up(
            pygame.K_UP, lambda e: self.camera_controller.move_up(False)
        )
        self.input_handler.on_key_up(
            pygame.K_RIGHT, lambda e: self.camera_controller.move_right(False)
        )
        self.input_handler.on_key_up(
            pygame.K_DOWN, lambda e: self.camera_controller.move_down(False)
        )
        self.input_handler.on_key_up(
            pygame.K_LEFT, lambda e: self.camera_controller.move_left(False)
        )
        self.input_handler.on_key_down(
            pygame.K_UP, lambda e: self.camera_controller.move_up(True)
        )
        self.input_handler.on_key_down(
            pygame.K_RIGHT, lambda e: self.camera_controller.move_right(True)
        )
        self.input_handler.on_key_down(
            pygame.K_DOWN, lambda e: self.camera_controller.move_down(True)
        )
        self.input_handler.on_key_down(
            pygame.K_LEFT, lambda e: self.camera_controller.move_left(True)
        )
        self.input_handler.on_key_up(
            pygame.K_SPACE, lambda e: self._toggle_simulation_running()
        )

    def _step_simulation(self) -> None:
        self.sim.step()

    def _handle_button_click(self, event: pygame.event.Event) -> None:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.ui_elements["step-btn"]:
                self._step_simulation()
            if event.ui_element == self.ui_elements["play-btn"]:
                self.sim_running = True
            if event.ui_element == self.ui_elements["pause-btn"]:
                self.sim_running = False

    def _handle_mouse_click(self, event: pygame.event.Event) -> None:
        mouse_screen_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        mouse_camera_offset = (
            pygame.math.Vector2(
                self.display.get_width() // 2, self.display.get_height() // 2
            )
            - self.camera.position
        )
        mouse_pos = mouse_screen_pos - mouse_camera_offset

        # Check if the user clicked a building
        for place_sprite in self.places_group.get_places():
            if place_sprite.rect and place_sprite.rect.collidepoint(
                mouse_pos.x, mouse_pos.y
            ):
                PlaceInfoWindow(place_sprite.place, self.sim, self.ui_manager)
                return

    def _toggle_simulation_running(self) -> None:
        self.sim_running = not self.sim_running

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle PyGame events while active"""
        self.input_handler.emit(event)
        return True


class Game:
    """
    Simple class that runs the game

    Attributes
    ----------
    config: GameConfig
        Configuration settings for the game
    display: pygame.Surface
        The surface that is drawn on by the scene
    window: pygame.Surface
        The surface representing the PyGame window
    clock: pygame.time.Clock
        Manages the time between frames
    running: boolean
        Remains True while the game is running
    ui_manager: pygame_gui.UIManager
        Manages all the UI windows and elements
    scene: GameScene
        The current scene being updated and drawn to the display
    """

    __slots__ = "config", "display", "window", "clock", "running", "ui_manager", "scene"

    def __init__(self, config: GameConfig) -> None:
        pygame.init()
        self.config: GameConfig = config
        self.display: pygame.Surface = pygame.Surface((config.width, config.height))
        self.window: pygame.Surface = pygame.display.set_mode(
            (config.width, config.height)
        )
        pygame.display.set_caption("Neighborly PyGame Sample")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = False
        self.ui_manager: pygame_gui.UIManager = pygame_gui.UIManager(
            (config.width, config.height)
        )
        self.scene: Scene = GameScene(self.display, self.ui_manager, config)

    def update(self, delta_time: float) -> None:
        """Update the active scene"""
        self.ui_manager.update(delta_time)
        self.scene.update(delta_time)

    def draw(self) -> None:
        """Draw the current scene"""
        self.scene.draw()
        self.ui_manager.draw_ui(self.display)
        self.window.blit(self.display, (0, 0))
        pygame.display.update()

    def handle_events(self):
        """Active mode handles PyGame events"""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.quit()
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                    continue

            if self.ui_manager.process_events(event):
                continue

            self.scene.handle_event(event)

    def run(self) -> None:
        """Main game loop"""
        self.running = True
        while self.running:
            time_delta = self.clock.tick(self.config.fps) / 1000.0
            self.handle_events()
            self.update(time_delta)
            self.draw()
        pygame.quit()

    def quit(self) -> None:
        """Stop the game"""
        self.running = False


def main():
    config = GameConfig(width=1024, height=768, fps=60, show_debug=True)

    game = Game(config)

    game.run()


if __name__ == "__main__":
    main()
