from krita import DockWidget

from version_manager import qt_docker_widget_ui
from PyQt5 import QtWidgets

from .utils import Utils
import version_manager.utils as utils
import version_manager.version_manager as VM

import time


class QtDocker(DockWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Document Version Manager')

        self.setWidget(QtDockerWidget())

    def canvasChanged(self, canvas):
        pass


class QtDockerWidget(QtWidgets.QWidget, qt_docker_widget_ui.Ui_Form):

    def __init__(self, parent=None):
        super(QtDockerWidget, self).__init__(parent)
        self.setupUi(self)

        self.reload_modules_widget.clicked.connect(self.reload_modules)
        self.add_checkpoint_btn.clicked.connect(self.add_checkpoint)

    def add_checkpoint(self, s):
        from importlib import reload
        reload(VM)
        # vm = VM.VersionManager(self.textbox)
        vm = VM.VersionManager()
        vm.info_update.connect(self.info_update)

        try:
            vm.add_checkpoint(msg=self.checkpoint_msg.text(),
                              autosave=self.autosave.checkState() == 2,
                              generate_thumbnail=self.generate_thumbnail.checkState() == 2
                              )
            self.info_update('Add Checkpoint successfully completed.')
        except Exception as e:
            self.info_update(str(e))
            self.message_box(str(e), 'Error - Operation Failed')

    def info_update(self, msg):
        current_time = time.strftime('%H:%M:%S', time.localtime())
        self.textbox.append(f'{current_time} {msg}')

    def reload_modules(self):
        from importlib import reload

        import version_manager.utils
        reload(version_manager.utils)
        version_manager.utils.doit()

        import version_manager.version_manager
        reload(version_manager.version_manager)
        version_manager.version_manager.doit()

    def message_box(self, msg, title=None):

        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText(msg)

        if title:
            msgBox.setWindowTitle(str(title))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
