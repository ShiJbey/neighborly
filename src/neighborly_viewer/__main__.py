"""
Neighborly viewer is the GUI application companion
to the simulation. It is built using PyQt6 and
allows users to inspect and export simulation data.
"""
import sys

from PyQt6 import QtWidgets
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QApplication, QMainWindow

from neighborly_viewer.main_window import Ui_MainWindow as NeighborlyViewerWindow


def prep_model():
    entries = ["one", "two", "three"]

    model = QStandardItemModel()

    for i in entries:
        item = QStandardItem(i)
        model.appendRow(item)

    return model


def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = NeighborlyViewerWindow()
    ui.setupUi(window)
    ui.listView.setModel(prep_model())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
