import threading
import time
from enum import Enum
from typing import Optional, Protocol

import ipywidgets as widgets
from IPython.display import display

from neighborly.simulation import Simulation


class SimulationGUIWidget(Protocol):
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError()


class GameCharacterWidget:
    """Displays information about a GameCharacter instance"""

    ...


class LocationWidget:
    """Displays information about a Location instance"""

    ...


class RoutineWidget:
    """Displays information about a Routine instance"""

    ...


class RelationshipWidget:
    """Displays information about a Relationship instance"""


class SimulationState(Enum):
    """Tracks if the simulation is running or paused"""

    PAUSED = 0
    STEPPING = 1
    RUNNING = 2
    STOPPED = 3


def create_character_tab():
    """Create the GUI tab that"""


class SimulationGUI:
    """Ipywidget GUI that displays information about a Neighborly Simulation instance"""

    def __init__(self, simulation: Simulation) -> None:
        self.simulation: Simulation = simulation
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_running = True
        self.simulation_paused = True
        self.simulation_stepping = False
        self.active_widget: Optional[SimulationGUIWidget] = None

        # Create GUI
        self.date_text = widgets.Text(
            value=self.simulation.time.to_date_str(),
            disabled=True,
            layout=widgets.Layout(width="100%"),
        )

        self.play_button = widgets.Button(
            description="Play",
            disabled=False,
        )
        self.play_button.on_click(self.play_simulation)

        self.step_button = widgets.Button(
            description="Step",
            disabled=False,
        )
        self.step_button.on_click(self.step_simulation)

        self.pause_button = widgets.Button(
            description="Pause",
            disabled=True,
        )
        self.pause_button.on_click(self.pause_simulation)

        self.characters_tab = widgets.VBox(
            [widgets.HTML(value=f"<h1>Characters</h1>")]
        )  # type: ignore
        self.places_tab = widgets.VBox(
            [widgets.HTML(value=f"<h1>Places</h1>")]
        )  # type: ignore

        tabs = widgets.Tab([self.characters_tab, self.places_tab])  # type: ignore
        tabs.set_title(0, "Characters")
        tabs.set_title(1, "Places")

        self.root_widget = widgets.VBox(
            [
                widgets.HBox(
                    [self.play_button, self.step_button, self.pause_button]
                ),  # type: ignore
                self.date_text,
                tabs,
            ],
            layout=widgets.Layout(width="80%", padding="12px"),
        )  # type: ignore

    def update_gui(self):
        self.date_text.value = self.simulation.time.to_date_str()
        if self.active_widget:
            self.active_widget.update()

    def run_simulation(self):
        while self.simulation_running:
            if not self.simulation_paused or self.simulation_stepping:
                self.simulation.step()
                self.update_gui()
                self.simulation_stepping = False
            time.sleep(0.05)

    def play_simulation(self, b):
        self.simulation_paused = False
        self.play_button.disabled = True
        self.pause_button.disabled = False
        self.step_button.disabled = True

    def step_simulation(self, b):
        self.simulation_stepping = True

    def pause_simulation(self, b):
        self.simulation_paused = True
        self.pause_button.disabled = True
        self.play_button.disabled = False
        self.step_button.disabled = False

    def run(self) -> None:
        display(self.root_widget)
        self.simulation_thread.start()
