from krita import DockWidget
from PyQt5.QtWidgets import QFileDialog

from .utils import Utils


class VersionManagerDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Version Manager")

    def canvasChanged(self, canvas):
        pass
