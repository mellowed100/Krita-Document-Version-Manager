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

        self._version_ui = VersionUI()

        self.setWidget(self._version_ui)

        self.active_doc = None

    def canvasChanged(self, canvas):
        """Reload the version manager if the active document changes"""

        doc = Krita.instance().activeDocument()

        if not self.active_doc or self.active_doc.fileName() != doc.fileName():
            self.active_doc = doc
            self._version_ui.info_update('Switching documents')
            self._version_ui.reload_history()


class VersionUI(QtWidgets.QWidget, qt_docker_widget_ui.Ui_Form):
    """Widget containing document version history and new checkpoint widgets"""

    def __init__(self, parent=None):
        super(VersionUI, self).__init__(parent)
        self.setupUi(self)

        self.add_checkpoint_btn.clicked.connect(self.add_checkpoint)
        self.history_widget.info_update.connect(self.info_update)
        self.history_widget.error_update.connect(self.report_error)

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
            self.report_error(str(e), 'Error - Operation Failed')
            return

    def report_error(self, msg, title='Error - Operation Failed'):
        self.info_update(str(msg))
        self.message_box(str(msg), 'Error - Operation Failed')

    def info_update(self, msg):
        current_time = time.strftime('%H:%M:%S', time.localtime())
        self.debug_console.append(f'{current_time}  {msg}')

    def message_box(self, msg, title=None):

        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText(msg)

        if title:
            msgBox.setWindowTitle(str(title))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
