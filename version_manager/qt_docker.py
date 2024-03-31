from krita import DockWidget
from version_manager.qt_docker_widget import QtDockerWidget


class QtDocker(DockWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Document Version Manager')

        self.setWidget(QtDockerWidget())

    def canvasChanged(self, canvas):
        pass
