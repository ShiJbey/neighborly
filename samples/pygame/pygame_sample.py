import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union, cast

import pygame
import pygame_gui

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import AbstractFactory, ComponentDefinition
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.loaders import YamlDataLoader
from neighborly.simulation import NeighborlyConfig, Simulation

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

# Character sprite width in pixels
CHARACTER_SIZE = 12

SMALL_PLACE_SIZE = (5, 5)
MEDIUM_PLACE_SIZE = (7, 10)
LARGE_PLACE_SIZE = (10, 15)

# Number of pixels between lots
LOT_PADDING = 36


class Building(Component):
    __slots__ = "size", "capacity"

    def __init__(self, size: str) -> None:
        super().__init__()
        self.size = size
        if size == "small":
            self.size = SMALL_PLACE_SIZE
        elif size == "medium":
            self.size = MEDIUM_PLACE_SIZE
        elif size == "large":
            self.capacity = LARGE_PLACE_SIZE
        else:
            raise ValueError("Invalid building size")

    def on_start(self) -> None:
        location = self.gameobject.get_component(Location)
        location.max_capacity = self.size[0] * self.size[1]

    def __repr__(self) -> str:
        return f"Building(size={self.size}, capacity={self.capacity})"


class BuildingFactory(AbstractFactory):
    def __init__(self):
        super().__init__("Building")

    def create(self, world: World, **kwargs) -> Building:
        return Building(kwargs.get("size", "small"))


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


class CharacterSprite(pygame.sprite.Sprite):
    __slots__ = (
        "character",
        "image",
        "rect",
        "position",
        "speed",
        "previous_destination",
        "destination",
    )

    def __init__(
        self, character: GameObject, color: Tuple[int, int, int] = CHARACTER_COLOR
    ) -> None:
        super().__init__()
        self.character: GameObject = character
        self.image: pygame.Surface = pygame.Surface([CHARACTER_SIZE, CHARACTER_SIZE])
        self.image.fill(color)
        self.rect: pygame.Rect = self.image.get_rect()
        self.position: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
        self.rect.topleft = (round(self.position.x), round(self.position.y))
        self.speed: int = 2000
        self.previous_destination: Optional[Tuple[int, int, pygame.math.Vector2]] = None
        self.destination: Optional[Tuple[int, int, pygame.math.Vector2]] = None

    def set_position(self, x: float, y: float):
        self.position.x = x
        self.position.y = y
        self.rect.topleft = (round(self.position.x), round(self.position.y))

    def update(self, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        if self.destination and self.rect:
            _, _, destination_pos = self.destination

            move: pygame.math.Vector2 = destination_pos - self.position
            move_length: float = move.length()

            if move_length < self.speed * delta_time:
                self.position = destination_pos
                self.previous_destination = self.destination
                self.destination = None
            elif move_length != 0:
                move.normalize_ip()
                move = move * self.speed * delta_time
                self.position += move

            self.rect.topleft = (round(self.position.x), round(self.position.y))


class OccupancyGrid:
    """Manages where characters can stand at a location"""

    def __init__(self, width: int, length: int) -> None:
        self._width = width
        self._length = length
        self._spaces: List[bool] = [False] * width * length
        self._unoccupied: List[int] = list(range(0, width * length))
        self._occupied: Set[int] = set()

    def get_size(self) -> int:
        return self._width * self._length

    def has_vacancy(self) -> bool:
        return bool(self._unoccupied)

    def set_next(self) -> Tuple[int, pygame.math.Vector2]:
        index = self._unoccupied.pop()
        self._occupied.add(index)
        x: int = index // self._length
        y: int = index % self._length
        return index, pygame.math.Vector2(x, y)

    def unset(self, index: int) -> None:
        self._unoccupied.append(index)
        self._occupied.remove(index)
        self._spaces[index] = False

    def __getitem__(self, pos: pygame.math.Vector2) -> bool:
        return self._spaces[int(pos.x * self._length + pos.y)]


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
        width = place.get_component(Building).size[0]
        height = place.get_component(Building).size[1]
        self.image = pygame.Surface([width * CHARACTER_SIZE, height * CHARACTER_SIZE])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        pos = place.get_component(Position2D)
        self.position = pygame.Vector2(
            LOT_PADDING + pos.x * (LARGE_PLACE_SIZE[0] * CHARACTER_SIZE + LOT_PADDING),
            LOT_PADDING + pos.y * (LARGE_PLACE_SIZE[1] * CHARACTER_SIZE + LOT_PADDING),
        )

        self.rect.topleft = (round(self.position.x), round(self.position.y))

        self.font = pygame.font.SysFont("Arial", 12)
        # self.textSurf = self.font.render(
        #     place.name, True, (255, 255, 255), (0, 0, 0, 255)
        # )
        # text_width = self.textSurf.get_width()
        # text_height = self.textSurf.get_height()
        # self.image.blit(
        #     self.textSurf,
        #     [
        #         (width * CHARACTER_SIZE) / 2 - text_width / 2,
        #         (height * CHARACTER_SIZE) / 2 - text_height / 2,
        #     ],
        # )

        self.occupancy: OccupancyGrid = OccupancyGrid(width, height)

    def get_available_space(self) -> Tuple[int, pygame.math.Vector2]:
        if self.occupancy.has_vacancy():
            index, pos = self.occupancy.set_next()
            pos_x = pos.x * CHARACTER_SIZE + self.position.x
            pos_y = pos.y * CHARACTER_SIZE + self.position.y
            sprite_pos = pygame.math.Vector2(pos_x, pos_y)
            return index, sprite_pos

    def free_space(self, space: int) -> None:
        self.occupancy.unset(space)


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


class CharacterSpriteGroup(pygame.sprite.Group):
    def __init__(
        self,
        surface: pygame.Surface,
        *sprites: Union[CharacterSprite, Sequence[CharacterSprite]],
    ) -> None:
        super().__init__(*sprites)
        self.surface = surface
        self.half_width = self.surface.get_width() // 2
        self.half_height = self.surface.get_height() // 2
        self.offset = pygame.math.Vector2()

    def get_characters(self) -> List[CharacterSprite]:
        return cast(List[CharacterSprite], self.sprites())

    def custom_draw(self, camera_focus: pygame.math.Vector2) -> None:
        self.offset.x = camera_focus.x - self.half_width
        self.offset.y = camera_focus.y - self.half_height

        for sprite in self.sprites():
            if sprite.rect and sprite.image:
                offset_pos = pygame.math.Vector2(sprite.rect.topleft) - self.offset
                self.surface.blit(sprite.image, offset_pos)

    def navigation_complete(self) -> bool:
        for sprite in self.get_characters():
            if sprite.destination is not None:
                return False
        return True


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


class GameScene:
    def __init__(
        self,
        display: pygame.Surface,
        ui_manager: pygame_gui.UIManager,
        config: GameConfig,
    ) -> None:
        self.display = display
        self.background = pygame.Surface((config.width, config.height))
        self.background.fill(BACKGROUND_COLOR)
        self.ui_manager = ui_manager
        self.character_group = CharacterSpriteGroup(display)
        self.places_group = PlacesSpriteGroup(display)
        self.background_group = YSortCameraGroup(display)

        self.camera_focus = pygame.math.Vector2()
        self.camera_speed = 300
        self.input_state = {"up": False, "right": False, "down": False, "left": False}

        self.sim = self._init_sim()
        self.sim_running = False

        self._create_background(
            self.background_group,
            (
                self.sim.config.simulation.town.width,
                self.sim.config.simulation.town.length,
            ),
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
            text=f"Town: {self.sim.get_town().name}, Date: {self.sim.time.to_date_str()}",
            manager=self.ui_manager,
            container=self.info_panel,
            parent_element=self.info_panel,
        )

    @staticmethod
    def _init_sim() -> Simulation:
        NEIGHBORLY_CONFIG = NeighborlyConfig(
            **{
                "simulation": {
                    "seed": random.randint(0, 999999),
                    "hours_per_timestep": 6,
                    "start_date": "0000-00-00T00:00.000z",
                    "end_date": "0060-00-00T00:00.000z",
                    "days_per_year": 10,
                },
                "plugins": [
                    "neighborly.plugins.talktown",
                ],
            }
        )
        sim = Simulation(NEIGHBORLY_CONFIG)
        YamlDataLoader(
            filepath=Path(os.path.abspath(__file__)).parent / "data.yaml"
        ).load(sim.engine)
        sim.engine.add_component_factory(BuildingFactory())

        return sim

    @staticmethod
    def _create_background(
        sprite_group: pygame.sprite.Group, town_size: Tuple[int, int]
    ) -> None:
        ground = BoxSprite(
            GROUND_COLOR,
            town_size[0] * LARGE_PLACE_SIZE[0] * CHARACTER_SIZE
            + LOT_PADDING * (town_size[0] + 1),
            town_size[1] * LARGE_PLACE_SIZE[1] * CHARACTER_SIZE
            + LOT_PADDING * (town_size[1] + 1),
        )
        sprite_group.add(ground)

        for row in range(town_size[1]):
            y_offset = LOT_PADDING + row * (
                LARGE_PLACE_SIZE[1] * CHARACTER_SIZE + LOT_PADDING
            )
            for col in range(town_size[0]):
                x_offset = LOT_PADDING + col * (
                    LARGE_PLACE_SIZE[0] * CHARACTER_SIZE + LOT_PADDING
                )
                lot_sprite = BoxSprite(
                    LOT_COLOR,
                    LARGE_PLACE_SIZE[0] * CHARACTER_SIZE,
                    LARGE_PLACE_SIZE[1] * CHARACTER_SIZE,
                    x_offset,
                    y_offset,
                )
                sprite_group.add(lot_sprite)

    def draw(self) -> None:
        """Draw to the screen while active"""
        self.display.blit(self.background, (0, 0))
        self.background_group.custom_draw(self.camera_focus)
        self.places_group.custom_draw(self.camera_focus)
        self.character_group.custom_draw(self.camera_focus)
        self.ui_manager.draw_ui(self.display)

    def update(self, delta_time: float) -> None:
        """Update the state of the scene"""

        # Update the camera position
        if self.input_state["up"]:
            self.camera_focus += pygame.Vector2(0, -1) * delta_time * self.camera_speed
        if self.input_state["left"]:
            self.camera_focus += pygame.Vector2(-1, 0) * delta_time * self.camera_speed
        if self.input_state["down"]:
            self.camera_focus += pygame.Vector2(0, 1) * delta_time * self.camera_speed
        if self.input_state["right"]:
            self.camera_focus += pygame.Vector2(1, 0) * delta_time * self.camera_speed

        # Update the sprites (also remove sprites for deleted entities)
        self.character_group.update(delta_time=delta_time)
        self.places_group.update(delta_time=delta_time)

        # Only update the simulation when the simulation is running
        # and the characters are no longer moving
        if self.sim_running and self.character_group.navigation_complete():
            self.step_simulation()

            # TODO: Add a procedure for adding place and character sprites.
            #       For now, just take the set difference between the groups
            #       and the state of the ECS. Then create new sprites with those.

            existing_characters: Set[int] = set(
                map(lambda res: res[0], self.sim.world.get_component(GameCharacter))
            )

            entities_with_sprites: Set[int] = set(
                map(
                    lambda sprite: sprite.character.id,
                    self.character_group.get_characters(),
                )
            )

            new_character_entities = existing_characters - entities_with_sprites

            for entity in new_character_entities:
                self.character_group.add(
                    CharacterSprite(self.sim.world.get_gameobject(entity))
                )

            existing_places: Set[int] = set(
                map(lambda res: res[0], self.sim.world.get_component(Location))
            )

            places_with_sprites: Set[int] = set(
                map(lambda sprite: sprite.place.id, self.places_group.get_places())
            )

            new_place_entities = existing_places - places_with_sprites

            for entity in new_place_entities:
                self.places_group.add(
                    PlaceSprite(self.sim.world.get_gameobject(entity))
                )

            for character_sprite in self.character_group.get_characters():
                loc_id = character_sprite.character.get_component(
                    GameCharacter
                ).location
                if loc_id in self.places_group.sprite_dict:
                    loc = self.places_group.sprite_dict[loc_id]

                    if (
                        character_sprite.previous_destination
                        and character_sprite.previous_destination[0]
                        in self.places_group.sprite_dict
                    ):
                        previous_loc = self.places_group.sprite_dict[
                            character_sprite.previous_destination[0]
                        ]
                        previous_loc.free_space(
                            character_sprite.previous_destination[1]
                        )

                    destination_space, destination_pos = loc.get_available_space()
                    character_sprite.destination = (
                        loc_id,
                        destination_space,
                        destination_pos,
                    )

    def step_simulation(self) -> None:
        self.sim.step()

        self.info_panel_text.set_text(
            f"Town: {self.sim.get_town().name}, Date: {self.sim.time.to_date_str()}"
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle PyGame events while active"""
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            return True

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.ui_elements["step-btn"]:
                self.step_simulation()
                return True
            if event.ui_element == self.ui_elements["play-btn"]:
                self.sim_running = True
                return True
            if event.ui_element == self.ui_elements["pause-btn"]:
                self.sim_running = False
                return True

        if event.type == pygame.MOUSEBUTTONUP:
            # Get the mouse click position in world-space coordinates
            mouse_screen_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            mouse_camera_offset = (
                pygame.math.Vector2(
                    self.display.get_width() // 2, self.display.get_height() // 2
                )
                - self.camera_focus
            )
            mouse_pos = mouse_screen_pos - mouse_camera_offset

            # Check if the user clicked a character
            for character_sprite in self.character_group.get_characters():
                if character_sprite.rect and character_sprite.rect.collidepoint(
                    mouse_pos.x, mouse_pos.y
                ):
                    CharacterInfoWindow(
                        character_sprite.character, self.sim, self.ui_manager
                    )
                    return True

            # Check if the user clicked a building
            for place_sprite in self.places_group.get_places():
                if place_sprite.rect and place_sprite.rect.collidepoint(
                    mouse_pos.x, mouse_pos.y
                ):
                    PlaceInfoWindow(place_sprite.place, self.sim, self.ui_manager)
                    return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.input_state["up"] = True
                return True
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.input_state["left"] = True
                return True
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.input_state["down"] = True
                return True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.input_state["right"] = True
                return True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.input_state["up"] = False
                return True
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.input_state["left"] = False
                return True
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.input_state["down"] = False
                return True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.input_state["right"] = False
                return True
            if event.key == pygame.K_SPACE:
                self.sim_running = not self.sim_running
                return True

        return False


class Game:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.display = pygame.Surface((config.width, config.height))
        self.window = pygame.display.set_mode((config.width, config.height))
        pygame.display.set_caption("Neighborly PyGame Sample")
        self.clock = pygame.time.Clock()
        self.running = False
        self.ui_manager = pygame_gui.UIManager((config.width, config.height))
        self.scene = GameScene(self.display, self.ui_manager, config)

    def update(self, delta_time: float) -> None:
        """Update the active mode"""
        self.ui_manager.update(delta_time)
        self.scene.update(delta_time)

    def draw(self) -> None:
        """Draw the active game mode"""
        self.scene.draw()
        self.window.blit(self.display, (0, 0))
        pygame.display.update()

    def handle_events(self):
        """Active mode handles PyGame events"""
        for event in pygame.event.get():
            if self.ui_manager.process_events(event):
                continue

            if self.scene.handle_event(event):
                continue

            if event.type == pygame.QUIT:
                self.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    continue

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
        self.running = False


def main():
    pygame.init()

    config = GameConfig(1024, 768, 60, show_debug=True)

    game = Game(config)

    game.run()


if __name__ == "__main__":
    main()
