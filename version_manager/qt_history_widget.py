from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ast
import shutil
import krita
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from . import utils


class CheckFailed(Exception):
    pass


class HistoryModel(QtCore.QAbstractTableModel):
    def __init__(self, utils):
        """Table model for displaying document history.


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
    error_update = QtCore.pyqtSignal(str, str)

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
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)

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
            'Generate Thumbnail': 'generate_thumbnail_action',
            'Make Active': 'make_active',
            'Delete Checkpoint': 'delete_checkpoint',
            'Load Checkpoint': 'load_checkpoint',
            'Import Krita Image': 'import_krita'}

        for desc in self.context_menu_actions:
            self.context_menu.addAction(QtWidgets.QAction(desc, self))

    def report_error(self, msg, title):
        """Emits error_update signal to open error dialog"""
        self.error_update.emit(msg, title)

    def status_update(self, msg):
        """Emits info_update signal with message send to text box

        Parameters:
        msg (str) - Message to send
        """

        self.info_update.emit(msg)

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

        try:
            self.check_has_filename()
            self.check_modified_state()
            self.check_has_checkpoint()
        except CheckFailed as checkfail:
            self.report_error(str(checkfail), 'Checks failed')
            return

        current_doc = Krita.instance().activeDocument()

        old_date = self.model.history[doc_id]['date']

        filename = os.path.join(self.model.utils.data_dir,
                                self.model.history[doc_id]['dirname'],
                                self.model.history[doc_id]['filename'])
        if not os.path.exists(filename):
            raise FileNotFoundError(filename)

        self.status_update(
            f'copying {filename} -> {self.model.utils.krita_filename}')
        shutil.copyfile(filename, self.model.utils.krita_filename)

        self.status_update('closing old document')
        current_doc.close()

        self.status_update('Opening new document')
        new_doc = Krita.instance().openDocument(self.model.utils.krita_filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)

        self.add_checkpoint(msg=f'Copied from version: {old_date}',
                            autosave=True,
                            generate_thumbnail=True)
        self.reload_history()
        self.status_update('Finished making active')

    def generate_thumbnail_action(self, doc_id):
        """Generates new thumbnail image for given version.

        Parameters:
        doc_id (str) - Document ID for version to generate ID for.
        """

        thumbnail_src = os.path.join(self.model.utils.data_dir,
                                     self.model.history[doc_id]['dirname'],
                                     self.model.history[doc_id]['filename'])
        if not os.path.exists(thumbnail_src):
            raise FileNotFoundError(thumbnail_src)

        thumbnail_tgt = os.path.join(self.model.utils.data_dir,
                                     self.model.history[doc_id]['dirname'],
                                     'thumbnail.png')

        self.status_update(f'opening {thumbnail_src}')
        doc = Krita.instance().openDocument(thumbnail_src)

        self.status_update(f'Generating thumbnail {thumbnail_tgt}')
        self.generate_thumbnail(doc, thumbnail_tgt)
        doc.close()

        # update path to thumbnail in history.json if needed
        if self.model.history[doc_id]['thumbnail'] != 'thumbnail.png':
            vmutils = utils.Utils(Krita.instance().activeDocument().fileName())
            vmutils.lock_history()
            vmutils.read_history()
            vmutils.history[doc_id]['thumbnail'] = 'thumbnail.png'
            vmutils.write_history()
            vmutils.unlock_history()

        self.reload_history()
        self.status_update('Finished generating thumbnail')

    def delete_checkpoint(self, doc_id):
        """Deletes a checkpoint from the filesystem and history.json

        Parameters:
        doc_id (str) - Document ID key to delete
        """

        date = self.model.history[doc_id]['date']

        editor = QtWidgets.QDialog(self)

        layout = QtWidgets.QVBoxLayout()
        editor.setLayout(layout)

        for text in ('Are you sure you want to delete checkpoint:',
                     date,
                     '(There is no undo)'):
            label = QtWidgets.QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

        # create ok/cancel buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                             QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(editor.accept)
        buttons.rejected.connect(editor.reject)

        layout.addWidget(buttons)

        # show window and get result
        result = editor.exec()
        if not result:
            return

        vmutils = utils.Utils(Krita.instance().activeDocument().fileName())
        vmutils.read_history()

        if doc_id not in vmutils.history:
            raise IndexError(
                'Cannot find document id: {doc_id} in history.json')

        tgt_dir = os.path.join(vmutils.data_dir,
                               vmutils.history[doc_id]['dirname'])

        if not os.path.isdir(tgt_dir):
            raise FileNotFoundError(f'Document directory not found: {tgt_dir}')

        self.status_update(f'Removing document directory {tgt_dir}')
        vmutils.lock_history()
        vmutils.read_history()
        try:
            shutil.rmtree(tgt_dir)
            del vmutils.history[doc_id]
        except Exception as e:
            vmutils.unlock_history()
            self.report_error(str(e), 'Checkpoint delete failed')
            return
        vmutils.write_history()
        vmutils.unlock_history()
        self.reload_history()
        self.status_update('Checkpoint removal complete')

    def check_has_filename(self):
        """Checks that current document has filename.

        raises CheckFailException on failure
        """
        current_doc = Krita.instance().activeDocument()

        # check for new document that hasn't been saved yet
        if current_doc.fileName() == "":
            raise CheckFailed(
                "No filename found.\nPlease save the current document before creating a checkpoint")

    def check_modified_state(self, autosave=False):

        current_doc = Krita.instance().activeDocument()

        if not current_doc.modified():
            return

        if autosave:
            self.info_update.emit(
                'Auto-Save enabled. Saving document to {}'.format(current_doc.fileName()))
            current_doc.save()
            return

        msg = ''.join(['The current document has been modified.',
                       'Please save and create a checkpoint',
                       'before continuing the operation.'])

        raise CheckFailed(msg)

    def check_has_checkpoint(self):
        """Check if current document has a checkpoint in the version manager.

        Raises CheckFailed exception if no checkpoint found.
        """

        current_doc = Krita.instance().activeDocument()
        current_doc_id = str(utils.creation_date(current_doc.fileName()))

        if current_doc_id not in self.model.history:
            raise CheckFailed(''.join(['The current document currently ',
                                       'does not have a checkpoint.',
                                       'Please create one before continuing']))

    def import_krita(self, doc_id):
        """Imports a krita .kra into the version manager

        Parameters:
        doc_id (str) - unused
        """
        try:
            self.check_has_filename()
            self.check_modified_state()
            self.check_has_checkpoint()
        except CheckFailed as checkfail:
            self.report_error(str(checkfail), 'Checks failed')
            return

        # get name of krita file to import
        results = QtWidgets.QFileDialog.getOpenFileName(self,
                                                        'Import Krita Image',
                                                        self.model.utils.krita_dir,
                                                        'Krita Images(*.kra)')
        filename = results[0]

        # copy krita file to current document
        self.status_update(
            f'copying {filename} -> {self.model.utils.krita_filename}')
        shutil.copyfile(filename, self.model.utils.krita_filename)

        self.status_update('closing old document')
        current_doc = Krita.instance().activeDocument().close()

        # open current document
        self.status_update('Opening new document')
        new_doc = Krita.instance().openDocument(self.model.utils.krita_filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)

        self.add_checkpoint(msg=f'Imported krita file: {filename}',
                            autosave=True,
                            generate_thumbnail=True)
        self.reload_history()
        self.status_update('Finished making active')

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

        self.status_update('reloading document history')

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

    def add_checkpoint(self, msg='', autosave=False, generate_thumbnail=True):
        """Adds document checkpoint to data directory

        Parameters:
            msg (str) - checkpoint message
            autosave (bool) - Save the file first before creating checkpoint
        """
        try:
            self.check_has_filename()
            self.check_modified_state(autosave=autosave)
        except CheckFailed as checkfail:
            self.report_error(str(checkfail), 'Checks failed')
            return

        doc = Krita.instance().activeDocument()

        vmutils = utils.Utils(doc.fileName())

        # create data directory if this is the first check-point
        if not vmutils.data_dir_exists():
            self.info_update.emit(
                f'Initializing data directory {vmutils.data_dir}')
            vmutils.init()

        # Create new checkpoint
        doc_id, doc_data = vmutils.add_checkpoint(msg)

        if generate_thumbnail:
            filename = os.path.join(
                vmutils.data_dir, doc_data['dirname'], 'thumbnail.png')
            self.info_update.emit(f'Generating thumbnail: {filename}')
            self.generate_thumbnail(doc, filename)
            self.info_update.emit(
                'Updating document history with thumbnail information')
            vmutils.lock_history()
            vmutils.read_history()
            if doc_id not in vmutils.history:
                vmutils.unlock_history()
                raise KeyError(f'document {doc_id} not found in history json')
            doc_data = vmutils.history[doc_id]
            doc_data['thumbnail'] = 'thumbnail.png'
            vmutils.write_history()
            vmutils.unlock_history()

    def generate_thumbnail(self, doc, filename):
        """Opens a krita document and generates a new thumbnail images

        Parameters:
            doc (Krita static instance) - document to create clone of
            filename (str) - path to save generated thumbnail to.
        """

        clone = doc.clone()
        clone.setBatchmode(True)
        clone.flatten()

        target_dim = 240.0
        width = clone.width()
        height = clone.height()
        max_dim = max(width, height)
        scale_factor = target_dim/max_dim
        new_width = int(width*scale_factor)
        new_height = int(height*scale_factor)
        clone.scaleImage(new_width, new_height,
                         clone.resolution(), clone.resolution(), "box")
        self.info_update.emit(f'saving thumbnail to {filename}')
        clone.exportImage(filename, krita.InfoObject())
        clone.close()
