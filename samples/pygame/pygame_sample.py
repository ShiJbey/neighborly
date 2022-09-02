import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pprint import pprint
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union, cast

import pygame
import pygame_gui

from neighborly.core.building import Building
from neighborly.core.ecs import GameObject
from neighborly.core.position import Position2D
from neighborly.core.town import LandGrid
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.plugins.talktown import TalkOfTheTownPlugin
from neighborly.simulation import Simulation, SimulationBuilder
from samples.pygame.input_handler import InputHandler
from samples.pygame.settings import (
    BACKGROUND_COLOR,
    BUILDING_COLORS,
    BUILDING_SIZE,
    FRAMES_PER_SECOND,
    GROUND_COLOR,
    LOT_COLOR,
    LOT_PADDING,
    LOT_SIZE,
    SHOW_DEBUG_DATA,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    WORLD_SEED,
)
from samples.pygame.ui_windows import PlaceInfoWindow


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


class BuildingSprite(pygame.sprite.Sprite):
    """Sprite used to represent a place in the town"""

    def __init__(
        self,
        gameobject: GameObject,
        group: Optional[pygame.sprite.Group],
    ) -> None:
        super().__init__(group)
        self.gameobject = gameobject
        self.image = pygame.Surface((BUILDING_SIZE, BUILDING_SIZE))
        self.image.fill(
            BUILDING_COLORS.get(
                gameobject.get_component(Building).building_type, "white"
            )
        )
        self.rect = self.image.get_rect()
        pos = gameobject.get_component(Position2D)
        self.position = pygame.Vector2(
            LOT_PADDING + pos.x * (LOT_SIZE + LOT_PADDING),
            LOT_PADDING + pos.y * (LOT_SIZE + LOT_PADDING),
        )

        self.rect.topleft = (round(self.position.x), round(self.position.y))


class CameraSpriteGroup(pygame.sprite.Group):
    def __init__(
        self,
        surface: pygame.Surface,
        *sprites: Union[BuildingSprite, Sequence[BuildingSprite]],
    ) -> None:
        super().__init__(*sprites)
        self.surface = surface
        self.half_width = self.surface.get_width() // 2
        self.half_height = self.surface.get_height() // 2
        self.offset = pygame.math.Vector2()

    def get_buildings(self) -> List[BuildingSprite]:
        return cast(List[BuildingSprite], self.sprites())

    def custom_draw(self, camera_focus: pygame.math.Vector2) -> None:
        self.offset.x = camera_focus.x  # - self.half_width
        self.offset.y = camera_focus.y  # - self.half_height

        for sprite in self.sprites():
            if sprite.rect and sprite.image:
                offset_pos = pygame.math.Vector2(sprite.rect.topleft) - self.offset
                self.surface.blit(sprite.image, offset_pos)


class Scene(ABC):
    """
    Scenes manage the visuals and controls for the current state of the game

    Attributes
    ----------
    next: Scene
        The scene to transition to after this scene updates
    display_surface: pygame.Surface
        The surface representing the PyGame window
    """

    __slots__ = "next", "display_surface"

    def __init__(self) -> None:
        self.next: Scene = self
        self.display_surface: pygame.Surface = pygame.display.get_surface()

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
    """

    __slots__ = (
        "ui_manager",
        "camera",
        "camera_controller",
        "sim",
        "sim_status",
        "input_handler",
        "building_sprite_group",
        "background_group",
        "ui_elements",
        "info_panel",
        "info_panel_text",
        "all_sprites",
    )

    def __init__(self) -> None:
        super().__init__()
        self.all_sprites: CameraSpriteGroup = CameraSpriteGroup(self.display_surface)
        self.ui_manager: pygame_gui.UIManager = pygame_gui.UIManager(
            (self.display_surface.get_width(), self.display_surface.get_height())
        )
        self.sim: Simulation = (
            SimulationBuilder(
                seed=WORLD_SEED if WORLD_SEED else random.randint(0, 999999)
            )
            .add_plugin(DefaultPlugin())
            .add_plugin(TalkOfTheTownPlugin())
            .build()
        )
        self._setup()
        self.building_sprite_group: CameraSpriteGroup = CameraSpriteGroup(
            self.display_surface
        )
        self.camera: Camera = Camera()
        self.camera_controller: CameraController = CameraController(self.camera)
        self.input_handler: InputHandler = InputHandler()

        self.sim_status: SimulationStatus = SimulationStatus.STOPPED

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

        info_panel_rect = pygame.Rect((0, 0), (self.display_surface.get_width(), 50))
        info_panel_rect.bottomleft = (-self.display_surface.get_width(), 0)
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
            relative_rect=pygame.Rect((0, 0), (self.display_surface.get_width(), 50)),
            text=f"Town: {self.sim.town.name}, Date: {self.sim.time.to_date_str()}",
            manager=self.ui_manager,
            container=self.info_panel,
            parent_element=self.info_panel,
        )

        self._setup_input_handlers()

    def _setup(self) -> None:
        self._create_land_grid_sprites()

    def _create_land_grid_sprites(self) -> None:
        town_size = self.sim.world.get_resource(LandGrid).grid.shape

        ground = BoxSprite(
            GROUND_COLOR,
            town_size[0] * LOT_SIZE + LOT_PADDING * (town_size[0] + 1),
            town_size[1] * LOT_SIZE + LOT_PADDING * (town_size[1] + 1),
        )

        self.all_sprites.add(ground)

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
                self.all_sprites.add(lot_sprite)

    def draw(self) -> None:
        """Draw to the screen while active"""
        self.display_surface.fill(BACKGROUND_COLOR)
        self.all_sprites.custom_draw(self.camera.position)
        self.building_sprite_group.custom_draw(self.camera.position)
        self.ui_manager.draw_ui(self.display_surface)

    def update(self, delta_time: float) -> None:
        """Update the state of the scene"""
        self.all_sprites.update(delta_time)

        if self.sim_status == SimulationStatus.RUNNING:
            self.sim.step()
            print(self.sim.time.to_date_str())
        elif self.sim_status == SimulationStatus.STEPPING:
            self.sim.step()
            print(self.sim.time.to_date_str())
            self.sim_status = SimulationStatus.STOPPED

        self.building_sprite_group.empty()

        for gid, _ in self.sim.world.get_component(Building):
            self.building_sprite_group.add(
                BuildingSprite(
                    self.sim.world.get_gameobject(gid), self.building_sprite_group
                )
            )

        # Update the camera position
        self.camera_controller.update(delta_time)

        # Update the sprites (also remove sprites for deleted entities)
        self.building_sprite_group.update(delta_time=delta_time)

        # Update the UI
        self.info_panel_text.set_text(
            f"Town: {self.sim.town.name}, Date: {self.sim.time.to_date_str()}"
        )

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
        self.input_handler.on_key_up(pygame.K_SPACE, self._toggle_simulation_running)
        self.input_handler.on_key_up(pygame.K_TAB, self._step_simulation)

    def _step_simulation(self, event: pygame.event.Event) -> None:
        self.sim_status = SimulationStatus.STEPPING

    def _handle_button_click(self, event: pygame.event.Event) -> None:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.ui_elements["step-btn"]:
                self.sim_status = SimulationStatus.STEPPING
            if event.ui_element == self.ui_elements["play-btn"]:
                self.sim_status = SimulationStatus.RUNNING
            if event.ui_element == self.ui_elements["pause-btn"]:
                self.sim_status = SimulationStatus.STOPPED

    def _handle_mouse_click(self, event: pygame.event.Event) -> None:
        mouse_screen_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        mouse_camera_offset = self.camera.position * -1
        mouse_world_pos = mouse_screen_pos - mouse_camera_offset

        # Check if the user clicked a building
        for building_sprite in self.building_sprite_group.get_buildings():
            if building_sprite.rect and building_sprite.rect.collidepoint(
                mouse_world_pos.x, mouse_world_pos.y
            ):
                pprint(building_sprite.gameobject.to_dict())
                # PlaceInfoWindow(building_sprite.gameobject, self.sim, self.ui_manager)
                return

    def _toggle_simulation_running(self, event) -> None:
        if self.sim_status == SimulationStatus.RUNNING:
            self.sim_status = SimulationStatus.STOPPED
        else:
            self.sim_status = SimulationStatus.RUNNING

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
    window: pygame.Surface
        The surface representing the PyGame window
    clock: pygame.time.Clock
        Manages the time between frames
    running: boolean
        Remains True while the game is running
    scene: Scene
        The current scene being updated and drawn to the display
    """

    __slots__ = "config", "window", "clock", "running", "scene"

    def __init__(self, config: GameConfig) -> None:
        # Need to initialize pygame before anything else
        pygame.init()
        self.config: GameConfig = config
        self.window: pygame.Surface = pygame.display.set_mode(
            (config.width, config.height)
        )
        pygame.display.set_caption("Neighborly PyGame Sample")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = False
        self.scene: Scene = GameScene()

    def draw(self) -> None:
        """Draw the current scene"""
        self.scene.draw()
        pygame.display.update()

    def handle_events(self):
        """Active mode handles PyGame events"""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.quit()

            self.scene.handle_event(event)

    def run(self) -> None:
        """Main game loop"""
        self.running = True
        while self.running:
            self.handle_events()
            delta_time = self.clock.tick(self.config.fps) / 1000.0
            self.scene.update(delta_time)
            self.draw()
            # Swap to a different scene if the current scene
            # does not have itself listed as next
            self.scene = self.scene.next
        pygame.quit()

    def quit(self) -> None:
        """Stop the game"""
        self.running = False


def main():
    game = Game(
        GameConfig(
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            fps=FRAMES_PER_SECOND,
            show_debug=SHOW_DEBUG_DATA,
        )
    )

    game.run()


if __name__ == "__main__":
    main()
