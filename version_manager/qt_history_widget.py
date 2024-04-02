from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ast
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from . import utils


class HistoryModel(QtCore.QAbstractTableModel):
    def __init__(self, utils):
        """Table model dor displaying document history.


        column 0 = thumbnail
        column 1 = id (hidden)
        column 2 = date
        column 3 = checkpoint message

        Parameters:
            utils (version_manager.utils) - Version history data
        """
        super(HistoryModel, self).__init__()

        # version_manager.utils
        self._utils = utils

        # dictionary containing document history
        self._history = self._utils.history

        # 2D array of data for model
        self._data = [[self._history[key][property] for property in (
            'thumbnail', 'dirname', 'date', 'message')] for key in reversed(sorted(self._history))]

        # convert literal to original type
        for row in self._data:
            row[3] = ast.literal_eval(row[3])

        # Default thumbnail dimension
        self._default_dim = 240

        # Default thumbnail scaling factor
        self._thumbnail_scale = 1.0

    def data(self, index, role):

        # thumbnail column
        if index.column() == 0:

            # build path to thumbnail
            pixmap_filename = os.path.join(
                self._utils.data_dir, self._data[index.row()][1], self._data[index.row()][0])

            # quit if not file found
            if not os.path.isfile(pixmap_filename):
                return None

            # create and scale thumbnail
            pixmap = QtGui.QPixmap(pixmap_filename)
            scale_factor = int(self._default_dim * self._thumbnail_scale)
            pixmap = pixmap.scaledToWidth(scale_factor)

            if role == Qt.DecorationRole:
                return pixmap

            if role == Qt.SizeHintRole:
                return pixmap.size()

        if role == Qt.DisplayRole:
            # return text for thumbnail filename
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def setThumbnailScale(self, factor):
        """Resizes thumbnails.

        Parameters:
        factor (float) - Thumbnail scale multiplier."""

        self._thumbnail_scale = float(factor)
        self.dataChanged.emit(self.index(
            0, 0), self.index(0, self.rowCount(0)))


class HistoryWidget(QtWidgets.QWidget):
    """Widget showing version history for krita document

    Consists of a QTableView widget and a QSlider to adjust
    thumbnail scales.
    """

    # Signal to send text to debug console
    info_update = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.model = None

        self.table = QtWidgets.QTableView()
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)
        self.table.hideColumn(1)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        self.slider_widget = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_widget.valueChanged.connect(self.resize_thumbnails)
        self.slider_widget.setMinimum(10)
        self.slider_widget.setMaximum(300)
        self.slider_widget.setValue(64)
        layout.addWidget(self.slider_widget)

    def set_default_icon_scale(self):
        self.slider_widget.setValue(64)
        self.resize_thumbnails(64)

    def reload_history(self, doc):
        """Rebuilds model from document version history

        Parameters:
            doc (Krita.Document) - Document to get history from.
        """

        # remove existing model
        self.table.setModel(None)

        self.table.setDisabled(True)
        self.slider_widget.setDisabled(True)

        if not doc:
            return

        # check for new document that hasn't been saved yet
        if doc.fileName() == "":
            return

        self.info_update.emit('updating history widget')

        vmutils = utils.Utils(doc.fileName())

        vmutils.read_history()

        self.model = HistoryModel(vmutils)
        self.table.setModel(self.model)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)
        self.table.hideColumn(1)
        self.resize_thumbnails(self.slider_widget.value())

        self.table.setEnabled(True)
        self.slider_widget.setEnabled(True)

    def resize_thumbnails(self, s):
        """Slot to receive thumbnail resize events.

        Parameters:
        s (int) - New thumbnail width (in pixels)
        """

        if not self.model:
            return

        # update model with new thumbnail scale
        self.model.setThumbnailScale(float(s)/self.model._default_dim)

        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)

    def setColumnCount(self, n):
        '''Does nothing. Included here to be compatible with Designer generated gui'''
        pass

    def setRowCount(self, n):
        '''Does nothing. Included here to be compatible with Designer generated gui'''
        pass
