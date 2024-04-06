import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import json
from pprint import pprint


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        self._default_dim = 240
        self._thumbnail_scale = 1.0

    def data(self, index, role):

        if index.column() == 0:
            pixmap = QtGui.QPixmap(
                '/home/cesar/Dropbox/users/cesar/development/krita/version_manager/tests/.table_test.kra/doc_1711950409_3010845/thumbnail.png')
            pixmap = pixmap.scaledToWidth(
                int(self._default_dim * self._thumbnail_scale))

            if role == Qt.DecorationRole:
                return pixmap

            if role == Qt.SizeHintRole:
                return pixmap.size()

        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

    def setThumbnailScale(self, factor):
        self._thumbnail_scale = float(factor)


class HistoryWidget(QtWidgets.QWidget):
    def __init__(self, data_dir):
        super().__init__()

        self._data_dir = data_dir

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.table = QtWidgets.QTableView()

        with open('/home/cesar/Dropbox/users/cesar/development/krita/version_manager/tests/.table_test.kra/history.json', 'r') as infile:
            history = json.load(infile)

        model = [[history[key][property] for property in (
            'thumbnail', 'date', 'message')] for key in sorted(history)]
        pprint(model)

        self.model = TableModel(model)
        self.table.setModel(self.model)
        # self.table.setSizeAdjustPolicy(
        #     QtWidgets.QAbstractScrollArea.AdjustToContents)
        # self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)

        layout.addWidget(self.table)

        slider_widget = QtWidgets.QSlider(Qt.Horizontal)
        slider_widget.valueChanged.connect(self.resize_thumbnails)
        slider_widget.setMinimum(10)
        slider_widget.setMaximum(300)
        slider_widget.setValue(64)
        layout.addWidget(slider_widget)

    def resize_thumbnails(self, s):
        print(s)
        scale_factor = float(s)/240.0
        self.model.setThumbnailScale(scale_factor)
        self.model.dataChanged.emit(self.model.index(
            0, 0), self.model.index(0, self.model.rowCount(0)))

        self.table.resizeRowsToContents()
        # self.table.resizeColumnsToContents()
        # self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(0)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        history_widget = HistoryWidget()
        self.setCentralWidget(history_widget)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
