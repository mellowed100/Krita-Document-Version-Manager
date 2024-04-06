# SPDX-FileCopyrightText: © Cesar Velazquez <cesarve@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from PyQt5 import QtWidgets
from krita import DockWidget

from . import qt_docker_widget_ui
from .utils import Utils


class QtDocker(DockWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle('Document Version Manager')

        self._version_ui = VersionManager()

        self.setWidget(self._version_ui)

        self.active_doc = None

    def canvasChanged(self, canvas):
        """Reload the version manager if the active document changes"""

        doc = Krita.instance().activeDocument()

        if not self.active_doc or self.active_doc.fileName() != doc.fileName():
            self.active_doc = doc
            self._version_ui.info_update('Switching documents')
            self._version_ui.history_widget.reload_history()


class VersionManager(QtWidgets.QWidget, qt_docker_widget_ui.Ui_Form):
    """Widget containing document version history and new checkpoint widgets"""

    def __init__(self, parent=None):
        super(VersionManager, self).__init__(parent)
        self.setupUi(self)

        self.add_checkpoint_btn.clicked.connect(self.add_checkpoint)
        self.history_widget.info_update.connect(self.info_update)
        self.history_widget.error_update.connect(self.report_error)
        self.import_image.clicked.connect(self.history_widget.import_krita)

    def add_checkpoint(self, s):
        """Create a new document checkpoint"""

        try:
            self.history_widget.add_checkpoint(msg=self.checkpoint_msg.toPlainText(),
                                               autosave=self.autosave.checkState() == 2,
                                               generate_thumbnail=self.generate_thumbnail.checkState() == 2
                                               )

        except Exception as e:
            self.report_error(str(e), 'Error - Operation Failed')
            return

    def report_error(self, msg, title='Error - Operation Failed'):
        self.info_update(str(msg))
        self.message_box(str(msg), title)
        # raise Exception(str(msg))

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
