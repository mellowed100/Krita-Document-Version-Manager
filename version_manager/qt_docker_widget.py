from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from PyQt5 import QtWidgets
from krita import DockWidget

from . import qt_docker_widget_ui
from . import version_manager


class QtDocker(DockWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Document Version Manager')

        self._history = QtDockerWidget()

        self.setWidget(self._history)

        self.active_doc = None

        Krita.notifier().imageCreated.connect(self.imageCreated)

    def imageCreated(self, doc):
        # print('Image Created')
        pass

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

    def reload_history(self):
        """Reloads document history"""

        self.history_widget.reload_history()

    def add_checkpoint(self, s):
        """Create a new document checkpoint"""

        vm = version_manager.VersionManager()
        vm.info_update.connect(self.info_update)

        try:
            vm.add_checkpoint(msg=self.checkpoint_msg.toPlainText(),
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
        self.debug_console.append(f'{current_time}  {msg}')

    def reload_modules(self):
        from importlib import reload

        import version_manager.utils
        reload(version_manager.utils)

        import version_manager.version_manager
        reload(version_manager.version_manager)

        import version_manager.qt_history_widget
        reload(version_manager.qt_history_widget)
        version_manager.qt_history_widget.doit()

    def message_box(self, msg, title=None):

        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText(msg)

        if title:
            msgBox.setWindowTitle(str(title))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
