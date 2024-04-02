from krita import DockWidget

from version_manager import qt_docker_widget_ui
from PyQt5 import QtWidgets

from .utils import Utils
import version_manager.utils as utils
import version_manager.version_manager as VM
from . import qt_history_widget

import time


class QtDocker(DockWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Document Version Manager')

        self._history = QtDockerWidget()

        self.setWidget(self._history)

        self.active_doc = None

        Krita.notifier().imageCreated.connect(self.imageCreated)

    def imageCreated(self, doc):
        print('Image Created')

    def canvasChanged(self, canvas):
        doc = Krita.instance().activeDocument()

        if not self.active_doc or self.active_doc.fileName() != doc.fileName():
            self.active_doc = doc
            self._history.info_update('Switching documents')
            self._history.reload_history()


class QtDockerWidget(QtWidgets.QWidget, qt_docker_widget_ui.Ui_Form):

    def __init__(self, parent=None):
        super(QtDockerWidget, self).__init__(parent)
        self.setupUi(self)

        self.reload_modules_widget.clicked.connect(self.reload_modules)
        self.add_checkpoint_btn.clicked.connect(self.add_checkpoint)
        self.history_widget.info_update.connect(self.info_update)
        # self.history_widget.reload_history()

    def reload_history(self):
        doc = Krita.instance().activeDocument()
        self.history_widget.reload_history(doc)

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

            self.reload_history()

            self.info_update('Add Checkpoint successfully completed.')
        except Exception as e:
            self.info_update(str(e))
            self.message_box(str(e), 'Error - Operation Failed')

    def info_update(self, msg):
        current_time = time.strftime('%H:%M:%S', time.localtime())
        self.textbox.append(f'{current_time}  {msg}')

    def reload_modules(self):
        from importlib import reload

        import version_manager.utils
        reload(version_manager.utils)
        version_manager.utils.doit()

        import version_manager.version_manager
        reload(version_manager.version_manager)
        version_manager.version_manager.doit()

        import version_manager.qt_history_widget
        reload(version_manager.qt_history_widget)

    def message_box(self, msg, title=None):

        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText(msg)

        if title:
            msgBox.setWindowTitle(str(title))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
