import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from . import utils


class HistoryModel(QtCore.QAbstractTableModel):
    def __init__(self, utils):
        super(HistoryModel, self).__init__()

        self._utils = utils
        self._history = self._utils.history
        self._data = [[self._history[key][property] for property in (
            'thumbnail', 'dirname', 'date', 'message')] for key in reversed(sorted(self._history))]
        self._default_dim = 240
        self._thumbnail_scale = 1.0

    def data(self, index, role):

        if index.column() == 0:

            # build path to thumbnail
            pixmap_filename = os.path.join(
                self._utils.data_dir, self._data[index.row()][1], self._data[index.row()][0])
            print('bbbb', pixmap_filename)
            # quit if not file found
            if not os.path.isfile(pixmap_filename):
                return None

            pixmap = QtGui.QPixmap(pixmap_filename)
            scale_factor = int(self._default_dim * self._thumbnail_scale)
            print('cccc', scale_factor)
            pixmap = pixmap.scaledToWidth(scale_factor)

            if role == Qt.DecorationRole:
                return pixmap

            if role == Qt.SizeHintRole:
                return pixmap.size()

        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def setThumbnailScale(self, factor):
        self._thumbnail_scale = float(factor)


class HistoryWidget(QtWidgets.QWidget):

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

        # remove existing model
        self.table.setModel(None)

        # doc = Krita.instance().activeDocument()

        if not doc:
            return

        # check for new document that hasn't been saved yet
        if doc.fileName() == "":
            return

        self.info_update.emit('updating history widget')
        vmutils = utils.Utils(doc.fileName())

        try:
            vmutils.read_history()
        except Exception:
            return

        self.model = HistoryModel(vmutils)
        self.table.setModel(self.model)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)
        self.table.hideColumn(1)
        self.resize_thumbnails(self.slider_widget.value())

    def resize_thumbnails(self, s):
        if not self.model:
            return

        scale_factor = float(s)/240.0
        self.model.setThumbnailScale(scale_factor)
        self.model.dataChanged.emit(self.model.index(
            0, 0), self.model.index(0, self.model.rowCount(0)))

        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)

    def setColumnCount(self, n):
        # self.table.setColumnCount(n)
        pass

    def setRowCount(self, n):
        # elf.table.setRowCount(n)
        pass
