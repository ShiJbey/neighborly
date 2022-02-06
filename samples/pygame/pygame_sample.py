from dataclasses import dataclass
from typing import List, Optional, Tuple, Set, Union, Sequence, Dict

import pygame
import pygame_gui

from neighborly.loaders import YamlDataLoader
from neighborly.plugins import default_plugin
from neighborly.simulation import Simulation, SimulationConfig
from neighborly.core.character.character import GameCharacter

# COMMON COLORS
SKY_BLUE = (153, 218, 232)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
BUILDING_COLOR = (194, 194, 151)
BACKGROUND_COLOR = (232, 232, 213)

CHARACTER_SIZE = 12


class CharacterInfoWindow(pygame_gui.elements.UIWindow):
    """
    Wraps a pygame_ui panel to display information
    about a given character
    """

    def __init__(
        self, character_id: int, sim: Simulation, ui_manager: pygame_gui.UIManager
    ) -> None:
        character_comp = sim.world.component_for_entity(character_id, GameCharacter)
        super().__init__(
            pygame.Rect((10, 10), (320, 240)),
            ui_manager,
            window_display_title=str(character_comp.name),
            object_id=f"{character_id}",
        )
        self.ui_manager = ui_manager
        self.text = pygame_gui.elements.UITextBox(
            f"{sim.world.components_for_entity(character_id)}",
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
    def __init__(
        self,
        entity: int,
        color: Tuple[int, int, int],
        pos_x: int = 0,
        pos_y: int = 0,
    ) -> None:
        super().__init__()
        self.entity = entity
        self.image = pygame.Surface([CHARACTER_SIZE, CHARACTER_SIZE])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.position = pygame.Vector2(pos_x, pos_y)
        self.rect.topleft = (round(self.position.x), round(self.position.y))

        self.speed = 1000

        self.destination: Optional[pygame.Vector2] = None

    def update(self, **kwargs) -> None:
        delta_time: float = kwargs["delta_time"]
        if self.destination and self.rect:
            move = self.destination - self.position
            move_length = move.length()

            if move_length < self.speed * delta_time:
                self.position = self.destination
                self.destination = None
            elif move_length != 0:
                move.normalize_ip()
                move = move * self.speed * delta_time
                self.position += move

            self.rect.topleft = (round(self.position.x), round(self.position.y))


class OccupancyGrid:
    """Manages where characters can stand at a location"""

    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._spaces: List[bool] = [False] * width * height
        self._unoccupied: List[int] = list(range(0, width * height))
        self._occupied: Set[int] = set()

    def get_size(self) -> int:
        return self._width * self._height

    def has_vacancy(self) -> bool:
        return bool(self._unoccupied)

    def set_next(self) -> Tuple[int, int]:
        index = self._unoccupied.pop()
        self._occupied.add(index)
        row = int(index / self._height)
        col = index % self._height
        return row, col

    def unset(self, pos: Tuple[int, int]) -> None:
        index = pos[1] * self._width + pos[0]
        self._unoccupied.append(index)
        self._occupied.remove(index)
        self._spaces[index] = False

    def __getitem__(self, pos: Tuple[int, int]) -> bool:
        return self._spaces[pos[1] * self._width + pos[0]]


class PlaceSprite(pygame.sprite.Sprite):
    """Sprite used to represent a place in the town"""

    def __init__(
        self,
        name: str,
        color: Tuple[int, int, int],
        width_cu: int,
        height_cu: int,
        pos_x: int = 0,
        pos_y: int = 0,
    ) -> None:
        super().__init__()
        self.name = name
        width = width_cu * CHARACTER_SIZE
        height = height_cu * CHARACTER_SIZE
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.position = pygame.Vector2(pos_x, pos_y)
        self.rect.topleft = (round(self.position.x), round(self.position.y))

        self.font = pygame.font.SysFont("Arial", 12)
        self.textSurf = self.font.render(name, True, (255, 255, 255), (0, 0, 0, 255))
        W = self.textSurf.get_width()
        H = self.textSurf.get_height()
        self.image.blit(self.textSurf, [width / 2 - W / 2, height / 2 - H / 2])

        self.occupancy: OccupancyGrid = OccupancyGrid(width_cu, height_cu)

    def handle_character_move(self):
        if self.occupancy.has_vacancy():
            col, row = self.occupancy.set_next()
            pos_x = col * CHARACTER_SIZE + self.position.x
            pos_y = row * CHARACTER_SIZE + self.position.y
            pos = pygame.Vector2(pos_x, pos_y)
            return pos


class Camera:
    def __init__(self, speed: int = 300) -> None:
        self.focus = pygame.Vector2(0, 0)
        self.speed = speed

    def update(self, delta: pygame.math.Vector2) -> None:
        self.focus += delta * self.speed


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
        self.add()

    def custom_draw(self, camera_focus: pygame.math.Vector2) -> None:
        self.offset.x = camera_focus.x - self.half_width
        self.offset.y = camera_focus.y - self.half_height

        for sprite in sorted(
            self.sprites(), key=lambda s: s.rect.centery if s.rect else 0
        ):
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
        self.characters: List[CharacterSprite] = []
        self.buildings: List[PlaceSprite] = [
            PlaceSprite("Town Hall", BUILDING_COLOR, 24, 16, 300, 100),
            PlaceSprite("Home", BUILDING_COLOR, 5, 7, 500, 500),
        ]

        self.character_group = YSortCameraGroup(display)
        self.character_group.add(self.characters)
        self.building_group = YSortCameraGroup(display)
        self.building_group.add(self.buildings)
        self.camera_focus = pygame.math.Vector2()
        self.camera_speed = 300
        self.input_state = {"up": False, "right": False, "down": False, "left": False}

        self.sim = self._init_sim()
        self.sim_running = False

        for entity, character in self.sim.world.get_component(GameCharacter):
            # do something
            print(f"{entity}: {character}")
            sprite = CharacterSprite(entity, COLOR_BLUE)
            self.characters.append(sprite)
            self.character_group.add(sprite)

        self.open_windows: Dict[str, pygame_gui.elements.UIWindow] = {}
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
            text=f"Town: {self.sim.get_town().name}, Date: {self.sim.get_time().to_date_str()}",
            manager=self.ui_manager,
            container=self.info_panel,
            parent_element=self.info_panel,
        )

    @staticmethod
    def _init_sim() -> Simulation:

        STRUCTURES = """
        Places:
            Space Casino:
                Location:
                    activities: ["gambling", "drinking", "eating", "socializing"]
            Mars:
                Location:
                    activities: ["reading", "relaxing"]
            Kamino:
                Location:
                    activities: ["recreation", "studying"]
        """

        sim = Simulation(SimulationConfig(hours_per_timestep=4))
        default_plugin.initialize_plugin(sim.get_engine())
        YamlDataLoader(str_data=STRUCTURES).load(sim.get_engine())
        sim.create_town()

        # Add two characters
        sim.get_engine().create_character(sim.world, "Civilian")
        sim.get_engine().create_character(sim.world, "Civilian")

        return sim

    def draw(self) -> None:
        """Draw to the screen while active"""
        self.display.blit(self.background, (0, 0))
        self.building_group.custom_draw(self.camera_focus)
        self.character_group.custom_draw(self.camera_focus)
        self.ui_manager.draw_ui(self.display)

    def update(self, delta_time: float) -> None:
        """Update the state of the scene"""
        if self.input_state["up"]:
            self.camera_focus += pygame.Vector2(0, -1) * delta_time * self.camera_speed
        if self.input_state["left"]:
            self.camera_focus += pygame.Vector2(-1, 0) * delta_time * self.camera_speed
        if self.input_state["down"]:
            self.camera_focus += pygame.Vector2(0, 1) * delta_time * self.camera_speed
        if self.input_state["right"]:
            self.camera_focus += pygame.Vector2(1, 0) * delta_time * self.camera_speed
        self.character_group.update(delta_time=delta_time)

        if self.sim_running:
            self.step_simulation()

    def step_simulation(self) -> None:
        self.sim.step()

        self.info_panel_text.set_text(
            f"Town: {self.sim.get_town().name}, Date: {self.sim.get_time().to_date_str()}"
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
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + (
                self.camera_focus
                - pygame.math.Vector2(
                    self.display.get_width() // 2, self.display.get_height() // 2
                )
            )

            for character in self.characters:

                if character.rect and character.rect.collidepoint(
                    mouse_pos.x, mouse_pos.y
                ):
                    CharacterInfoWindow(character.entity, self.sim, self.ui_manager)

            # Check if the user clicked a building, if so get the building
            # and find the first available grid space and move the character
            # there if found
            for place in self.buildings:

                if place.rect and place.rect.collidepoint(mouse_pos.x, mouse_pos.y):
                    pos = place.handle_character_move()
                    if pos:
                        for character in self.characters:
                            character.destination = pos
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
        self.window.blit(self.display, (0, 0))
        self.scene.draw()
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
