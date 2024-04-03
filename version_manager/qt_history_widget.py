from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ast
import shutil
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from . import utils
from pprint import pprint


def doit():
    print('ttttttt')


class HistoryModel(QtCore.QAbstractTableModel):
    def __init__(self, utils):
        """Table model dor displaying document history.


        column 0 = key (hidden)
        column 1 = thumbnail
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
        self._data = [
            [
                key,
                self._history[key]['thumbnail'],
                self._history[key]['date'],
                ast.literal_eval(self._history[key]['message'])
            ]
            for key in reversed(sorted(self._history))]

        # Default thumbnail dimension
        self._default_dim = 240

        # Default thumbnail scaling factor
        self._thumbnail_scale = 1.0

    @property
    def history(self):
        """Dictionary holding document version data"""
        return self._history

    @property
    def utils(self):
        """version_manager.Utils instance"""
        return self._utils

    def data(self, index, role):

        # thumbnail column
        if index.column() == 1:

            # get dictionary key for current document in column 0
            key = self._data[index.row()][0]

            # build path to thumbnail
            pixmap_filename = os.path.join(
                self._utils.data_dir,
                self._history[key]['dirname'],
                self._history[key]['thumbnail'])

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
        self.table.resizeColumnToContents(1)  # thumbnail column
        self.table.hideColumn(0)  # key column
        # self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        # self.table = HistoryTable(self)

        layout.addWidget(self.table)

        self.slider_widget = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_widget.valueChanged.connect(self.resize_thumbnails)
        self.slider_widget.setMinimum(10)
        self.slider_widget.setMaximum(300)
        self.slider_widget.setValue(64)
        layout.addWidget(self.slider_widget)

        self.context_menu = QtWidgets.QMenu(self)

        self.context_menu_actions = {
            'Edit Checkpoint Message': 'edit_message',
            'Generate Thumbnail': 'generate_thumbnail',
            'Make Active': 'make_active',
            'Delete Checkpoint': 'delete_checkpoint',
            'Load Checkpoint': 'load_checkpoint'}

        for desc in self.context_menu_actions:
            self.context_menu.addAction(QtWidgets.QAction(desc, self))

    def context_menu(self, pos):
        """Display context menu in the history table"""

        # get document id for selected row
        row = self.table.verticalHeader().logicalIndexAt(pos)
        index = self.model.index(row, 0)
        doc_id = self.model.data(index, Qt.DisplayRole)

        # get context menu selection
        result = self.context_menu.exec_(QtGui.QCursor.pos())

        # nothing selected
        if not result:
            return

        # call menu item's method and pass document id
        getattr(self, self.context_menu_actions[result.text()])(doc_id)

    def edit_message(self, doc_id):
        """Opens dialog box to edit checkpoint message.

        Parameters:
        doc_id (str): document key in history dictionary
        """

        # get current message
        msg = self.model.history[doc_id]['message']

        editor = QtWidgets.QDialog(self)

        # create text box to edit checkpoint message
        text_box = QtWidgets.QPlainTextEdit()
        text_box.appendPlainText(ast.literal_eval(msg))

        # create ok/cancel buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                             QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(editor.accept)
        buttons.rejected.connect(editor.reject)

        # assemble widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(text_box)
        layout.addWidget(buttons)
        editor.setLayout(layout)

        # show window and get result
        result = editor.exec()
        if not result:
            return

        # get new checkpoint message
        new_msg = text_box.toPlainText()

        # check if msg is unchanged
        if msg == repr(new_msg):
            return

        # commit new message to disk
        self.model.utils.update_checkpoint_message(doc_id, new_msg)
        self.reload_history()

    def load_checkpoint(self, doc_id):
        """Loads a previous checkpoint into Krita

        Parameters:
        doc_id (str): document key to make active
        """

        current_doc = Krita.instance().activeDocument()

        filename = os.path.join(self.model.utils.data_dir,
                                self.model.history[doc_id]['dirname'],
                                self.model.history[doc_id]['filename'])
        if not os.path.exists(filename):
            raise FileNotFoundError(filename)

        new_doc = Krita.instance().openDocument(filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)

    def make_active(self, doc_id):
        """Makes a previous checkpoint the active document

        Parameters:
        doc_id (str): document key to make active
        """

        current_doc = Krita.instance().activeDocument()

        filename = os.path.join(self.model.utils.data_dir,
                                self.model.history[doc_id]['dirname'],
                                self.model.history[doc_id]['filename'])
        if not os.path.exists(filename):
            raise FileNotFoundError(filename)

        self.info_update(
            f'copying {filename} -> {self.model.utils.krita_filename}')
        shutil.copyfile(filename, self.model.utils.krita_filename)

        self.info_update('closing old document')
        current_doc.close()

        self.info_update('Opening new document')
        new_doc = Krita.instance().openDocument(self.model.utils.krita_filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)

    def generate_thumbnail(self, event):
        print('in generate thumbnail')

    def delete_checkpoint(self, doc_id):
        pass

    def set_default_icon_scale(self):
        self.slider_widget.setValue(64)
        self.resize_thumbnails(64)

    def reload_history(self):
        """Rebuilds model from current document version history"""

        doc = Krita.instance().activeDocument()

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
        self.table.resizeColumnToContents(1)
        self.table.hideColumn(0)
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
        self.table.resizeColumnToContents(1)

    def setColumnCount(self, n):
        '''Does nothing. Included here to be compatible with Designer generated gui'''
        pass

    def setRowCount(self, n):
        '''Does nothing. Included here to be compatible with Designer generated gui'''
        pass
