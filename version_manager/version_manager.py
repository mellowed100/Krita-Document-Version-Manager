from krita import DockWidget
from PyQt5.QtWidgets import QFileDialog


class VersionManagerDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Version Manager")
        print('AAAAA')

    def canvasChanged(self, canvas):
        pass
