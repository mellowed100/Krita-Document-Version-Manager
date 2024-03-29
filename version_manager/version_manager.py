from krita import *
from PyQt5.QtWidgets import QFileDialog


class VersionManagerDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Version Manager")

    def canvasChanged(self, canvas):
        pass


Krita.instance().addDockWidgetFactory(DockWidgetFactory(
    "myDocker", DockWidgetFactoryBase.DockRight, VersionManager))
