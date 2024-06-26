# SPDX-FileCopyrightText: © Cesar Velazquez <cesarve@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function, unicode_literals

import ast
import os
import shutil
import subprocess
import sys

import krita
from PyQt5 import QtCore, QtGui, QtWidgets

from . import utils

# default thumbnail resolution (in pixels)
default_thumbnail_resolution = 240

# default size of icon in gui (10-300)
default_thumbnail_scale = 64


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
                self._history[key]["thumbnail"],
                # "{}\n{}".format(self._history[key]["date"], key),
                "{}\n{}".format(self._history[key]["date"], self._history[key]["id"]),
                ast.literal_eval(self._history[key]["message"]),
            ]
            for key in reversed(sorted(self._history))
        ]

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
                self._history[key]["dirname"],
                self._history[key]["thumbnail"],
            )

            # quit if not file found
            if not os.path.isfile(pixmap_filename):
                return None

            # create and scale thumbnail
            pixmap = QtGui.QPixmap(pixmap_filename)
            scale_factor = int(default_thumbnail_resolution * self._thumbnail_scale)
            pixmap = pixmap.scaledToWidth(scale_factor)

            if role == QtCore.Qt.DecorationRole:
                return pixmap

            if role == QtCore.Qt.SizeHintRole:
                return pixmap.size()

        if index.column() == 2 and role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter

        if role == QtCore.Qt.DisplayRole:
            # return text for thumbnail filename
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        if self.rowCount(index) == 0:
            return 0
        return len(self._data[0])

    def setThumbnailScale(self, factor):
        """Resizes thumbnails.

        Parameters:
        factor (float) - Thumbnail scale multiplier."""

        self._thumbnail_scale = float(factor)
        self.dataChanged.emit(self.index(0, 0), self.index(0, self.rowCount(0)))


class HistoryWidget(QtWidgets.QWidget):
    """Table Widget showing version history for krita document

    Consists of a QTableView widget and a QSlider to adjust
    thumbnail scales.
    """

    # Signal to send text to debug console
    info_update = QtCore.pyqtSignal(str)
    error_update = QtCore.pyqtSignal(str, str)
    in_progress = QtCore.pyqtSignal(bool)

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
        self.table.resizeColumnToContents(2)  # date column
        self.table.hideColumn(0)  # key column
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)

        self.table.doubleClicked.connect(self.double_click_row)

        layout.addWidget(self.table)

        # create widget to encapsulate slider widgets
        self.icon_scale = QtWidgets.QWidget()
        icon_scale_layout = QtWidgets.QHBoxLayout()
        self.icon_scale.setLayout(icon_scale_layout)

        # setup icon scale decrement button
        button_dec = QtWidgets.QPushButton()
        icon_scale_layout.addWidget(button_dec)
        button_dec.setText("-")
        button_dec.setMaximumSize(20, 20)
        button_dec.clicked.connect(self.thumbnail_decrement)

        # setup icon scale slider
        self.slider_widget = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_widget.valueChanged.connect(self.resize_thumbnails)
        self.slider_widget.setMinimum(10)
        self.slider_widget.setMaximum(300)
        self.slider_widget.setValue(default_thumbnail_scale)
        icon_scale_layout.addWidget(self.slider_widget)

        # setup icon scale increment button
        button_inc = QtWidgets.QPushButton()
        icon_scale_layout.addWidget(button_inc)
        button_inc.setText("+")
        button_inc.setMaximumSize(20, 20)
        button_inc.clicked.connect(self.thumbnail_increment)

        layout.addWidget(self.icon_scale)

        # setup context menu
        self.context_menu = QtWidgets.QMenu(self)
        self.context_menu.setToolTipsVisible(True)

        self.context_menu_actions = {
            "Edit Checkpoint Message": {
                "func": "edit_message",
                "tooltip": "Make edits to checkpoint message.",
            },
            "Make Current": {
                "func": "make_checkpoint_current",
                "tooltip": "Make this checkpoint the current document",
            },
            "Load Checkpoint": {
                "func": "load_checkpoint",
                "tooltip": "Load checkpoint into Krita without making it the current document.",
            },
            "Generate Thumbnail": {
                "func": "generate_thumbnail_action",
                "tooltip": "Regenerates the thumbnail for this checkpoint",
            },
            "Delete Checkpoint": {
                "func": "delete_checkpoint",
                "tooltip": "Deletes this checkpoint from the version manager and file system",
            },
            "Show In File Browser": {
                "func": "show_in_browser",
                "tooltip": "Opens file browser on directory containing this checkpoint",
            },
        }

        for desc in self.context_menu_actions:
            action = QtWidgets.QAction(desc, self)
            action.setToolTip(self.context_menu_actions[desc]["tooltip"])
            self.context_menu.addAction(action)
            # self.context_menu.addAction(QtWidgets.QAction(desc, self))

    def double_click_row(self, index):
        """Loads a checkpoint when row is double clicked"""

        index = self.model.index(index.row(), 0)
        doc_id = self.model.data(index, QtCore.Qt.DisplayRole)

        self.load_checkpoint(doc_id)

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
        doc_id = self.model.data(index, QtCore.Qt.DisplayRole)

        # get context menu selection
        result = self.context_menu.exec_(QtGui.QCursor.pos())

        # nothing selected
        if not result:
            return

        # call menu item's method and pass document id
        getattr(self, self.context_menu_actions[result.text()]["func"])(doc_id)

    def edit_message(self, doc_id):
        """Opens dialog box to edit checkpoint message.

        Parameters:
        doc_id (str): document key in history dictionary
        """
        self.in_progress.emit(True)

        # get current message
        msg = self.model.history[doc_id]["message"]

        editor = QtWidgets.QDialog(self)

        # create text box to edit checkpoint message
        text_box = QtWidgets.QPlainTextEdit()
        text_box.appendPlainText(ast.literal_eval(msg))

        # create ok/cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
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
            self.in_progress.emit(False)
            return

        # get new checkpoint message
        new_msg = text_box.toPlainText()

        # check if msg is unchanged
        if msg == repr(new_msg):
            self.in_progress.emit(False)
            return

        # commit new message to disk
        self.model.utils.update_checkpoint_message(doc_id, new_msg)
        self.reload_history()
        self.in_progress.emit(False)

    def load_checkpoint(self, doc_id):
        """Loads a previous checkpoint into Krita

        Parameters:
        doc_id (str): document key to make active
        """

        self.in_progress.emit(True)
        current_doc = Krita.instance().activeDocument()

        filename = os.path.join(
            self.model.utils.data_dir,
            self.model.history[doc_id]["dirname"],
            self.model.history[doc_id]["filename"],
        )
        if not os.path.exists(filename):
            self.in_progress.emit(False)
            raise FileNotFoundError(filename)

        new_doc = Krita.instance().openDocument(filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)
        self.in_progress.emit(False)

    def make_checkpoint_current(self, doc_id):
        """Makes a previous checkpoint the current document

        Parameters:
        doc_id (str): document key to make active
        """

        self.in_progress.emit(True)
        try:
            self.check_has_filename()
            self.check_modified_state()
            self.check_has_checkpoint()
        except CheckFailed as checkfail:
            self.in_progress.emit(False)
            self.report_error(str(checkfail), "Checks failed")
            return

        current_doc = Krita.instance().activeDocument()
        active_filename = current_doc.fileName()

        old_date = self.model.history[doc_id]["date"]

        checkpoint_filename = os.path.join(
            self.model.utils.data_dir,
            self.model.history[doc_id]["dirname"],
            self.model.history[doc_id]["filename"],
        )
        if not os.path.exists(checkpoint_filename):
            self.in_progress.emit(False)
            raise FileNotFoundError(checkpoint_filename)

        self.status_update(f"copying {checkpoint_filename} -> {active_filename}")
        shutil.copyfile(checkpoint_filename, active_filename)

        self.status_update("closing old document")
        current_doc.close()

        self.status_update("Opening new document")
        new_doc = Krita.instance().openDocument(active_filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)

        old_message = ast.literal_eval(self.model.history[doc_id]["message"])
        self.add_checkpoint(
            msg=f"Copied from version:\n{old_date}\n\n{old_message}",
            autosave=True,
            generate_thumbnail=True,
        )
        self.reload_history()
        self.status_update("Finished making current")

        self.in_progress.emit(False)

    def generate_thumbnail_action(self, doc_id):
        """Generates new thumbnail image for given version.

        Parameters:
        doc_id (str) - Document ID for version to generate ID for.
        """

        self.in_progress.emit(True)
        thumbnail_src = os.path.join(
            self.model.utils.data_dir,
            self.model.history[doc_id]["dirname"],
            self.model.history[doc_id]["filename"],
        )
        if not os.path.exists(thumbnail_src):
            self.in_progress.emit(False)
            raise FileNotFoundError(thumbnail_src)

        thumbnail_tgt = os.path.join(
            self.model.utils.data_dir,
            self.model.history[doc_id]["dirname"],
            "thumbnail.png",
        )

        self.status_update(f"opening {thumbnail_src}")
        doc = Krita.instance().openDocument(thumbnail_src)

        self.status_update(f"Generating thumbnail {thumbnail_tgt}")
        self.generate_thumbnail(doc, thumbnail_tgt)
        doc.close()

        # update path to thumbnail in history.json if needed
        if self.model.history[doc_id]["thumbnail"] != "thumbnail.png":
            vmutils = utils.Utils(Krita.instance().activeDocument().fileName())
            vmutils.lock_history()
            vmutils.read_history()
            vmutils.history[doc_id]["thumbnail"] = "thumbnail.png"
            vmutils.write_history()
            vmutils.unlock_history()

        self.reload_history()
        self.status_update("Finished generating thumbnail")

        self.in_progress.emit(False)

    def delete_checkpoint(self, doc_id):
        """Deletes a checkpoint from the filesystem and history.json

        Parameters:
        doc_id (str) - Document ID key to delete
        """

        self.in_progress.emit(True)
        date = self.model.history[doc_id]["date"]

        editor = QtWidgets.QDialog(self)

        layout = QtWidgets.QVBoxLayout()
        editor.setLayout(layout)

        for text in (
            "Are you sure you want to delete checkpoint:",
            date,
            "(There is no undo)",
        ):
            label = QtWidgets.QLabel(text)
            label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(label)

        # create ok/cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(editor.accept)
        buttons.rejected.connect(editor.reject)

        layout.addWidget(buttons)

        # show window and get result
        result = editor.exec()
        if not result:
            self.in_progress.emit(True)
            return

        vmutils = utils.Utils(Krita.instance().activeDocument().fileName())
        vmutils.read_history()

        if doc_id not in vmutils.history:
            self.in_progress.emit(False)
            raise IndexError("Cannot find document id: {doc_id} in history.json")

        tgt_dir = os.path.join(vmutils.data_dir, vmutils.history[doc_id]["dirname"])

        if not os.path.isdir(tgt_dir):
            self.in_progress.emit(False)
            raise FileNotFoundError(f"Document directory not found: {tgt_dir}")

        self.status_update(f"Removing document directory {tgt_dir}")
        vmutils.lock_history()
        vmutils.read_history()
        try:
            shutil.rmtree(tgt_dir)
            del vmutils.history[doc_id]
        except Exception as e:
            self.in_progress.emit(False)
            vmutils.unlock_history()
            self.report_error(str(e), "Checkpoint delete failed")
            return
        vmutils.write_history()
        vmutils.unlock_history()
        self.reload_history()
        self.status_update("Checkpoint removal complete")

        self.in_progress.emit(False)

    def check_has_filename(self):
        """Checks that current document has filename.

        raises CheckFailException on failure
        """
        current_doc = Krita.instance().activeDocument()

        # check for new document that hasn't been saved yet
        if current_doc.fileName() == "":
            raise CheckFailed(
                "No filename found.\nPlease save the current document before creating a checkpoint"
            )

    def check_modified_state(self, autosave=False):
        """Check if current document has unsaved changes.

        Parameters:
        autosave (bool) - True, save the document if there are modifications

        Raises CheckFailed if there are unsaved modifications
        """

        current_doc = Krita.instance().activeDocument()

        if not current_doc.modified():
            return

        if autosave:
            self.status_update(
                "Auto-Save enabled. Saving document to {}".format(
                    current_doc.fileName()
                )
            )
            current_doc.save()
            return

        msg = "".join(
            [
                "The current document has been modified.",
                "Please save and create a checkpoint ",
                "before continuing the operation.",
            ]
        )

        raise CheckFailed(msg)

    def check_has_checkpoint(self):
        """Check if current document has a checkpoint in the version manager.

        Raises CheckFailed exception if no checkpoint found.
        """

        current_doc = Krita.instance().activeDocument()
        # current_doc_id = str(utils.creation_date(current_doc.fileName()))
        current_doc_id = str(os.path.getmtime(current_doc.fileName()))

        if current_doc_id not in self.model.history:
            raise CheckFailed(
                "".join(
                    [
                        "The current document currently ",
                        "does not have a checkpoint.",
                        "Please create one before continuing",
                    ]
                )
            )

    def import_krita(self):
        """Imports a krita .kra into the version manager"""
        self.in_progress.emit(True)
        try:
            self.check_has_filename()
            self.check_modified_state()
            self.check_has_checkpoint()
        except CheckFailed as checkfail:
            self.in_progress.emit(False)
            self.report_error(str(checkfail), "Checks failed")
            return

        # get name of krita file to import
        results = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Krita Image",
            self.model.utils.krita_dir,
            "Krita Images(*.kra)",
        )
        filename = results[0]

        # copy krita file to current document
        self.status_update(f"copying {filename} -> {self.model.utils.krita_filename}")
        shutil.copyfile(filename, self.model.utils.krita_filename)

        self.status_update("closing old document")
        current_doc = Krita.instance().activeDocument().close()

        # open current document
        self.status_update("Opening new document")
        new_doc = Krita.instance().openDocument(self.model.utils.krita_filename)
        Krita.instance().activeWindow().addView(new_doc)
        Krita.instance().setActiveDocument(new_doc)

        self.add_checkpoint(
            msg=f"Imported krita file: {filename}",
            autosave=True,
            generate_thumbnail=True,
        )
        self.reload_history()
        self.status_update("Finished import krita file.")
        self.in_progress.emit(False)

    def show_in_browser(self, doc_id):
        """Opens up system file browser on directory containing krita document

        Parameters:
        doc_id (str) - document id to load into file browser
        """
        self.in_progress.emit(False)
        try:
            self.check_has_filename()
            self.check_has_checkpoint()
        except CheckFailed as checkfail:
            self.in_progress.emit(False)
            self.report_error(str(checkfail), "Checks failed")
            return

        doc_dir = os.path.join(
            self.model.utils.data_dir, self.model.history[doc_id]["dirname"]
        )

        if sys.platform == "win32":
            subprocess.Popen(["start", doc_dir], shell=True)

        elif sys.platform == "darwin":
            subprocess.Popen(["open", doc_dir])

        else:
            try:
                subprocess.Popen(["xdg-open", doc_dir])
            except OSError:
                self.in_progress.emit(False)
                raise Exception("Unknown system")

        self.in_progress.emit(False)

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

        vmutils = utils.Utils(doc.fileName())

        # check for non-existing data directory
        if not vmutils.data_dir_exists():
            return

        self.status_update("reloading document history {}".format(doc.fileName()))

        vmutils.read_history()

        self.model = HistoryModel(vmutils)
        self.table.setModel(self.model)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(1)
        self.table.resizeColumnToContents(2)
        self.table.hideColumn(0)
        self.resize_thumbnails(self.slider_widget.value())

        self.table.setEnabled(True)
        self.slider_widget.setEnabled(True)

    def thumbnail_decrement(self):
        """Decrements icons scale slider by it page step"""

        page_step = self.slider_widget.pageStep()
        value = self.slider_widget.value()
        min_value = self.slider_widget.minimum()
        max_value = self.slider_widget.maximum()
        new_value = max(min_value, min(value - page_step, max_value))
        self.slider_widget.setValue(new_value)

    def thumbnail_increment(self):
        """Increments icons scale slider by it page step"""

        page_step = self.slider_widget.pageStep()
        value = self.slider_widget.value()
        min_value = self.slider_widget.minimum()
        max_value = self.slider_widget.maximum()
        new_value = max(min_value, min(value + page_step, max_value))
        self.slider_widget.setValue(new_value)

    def resize_thumbnails(self, s):
        """Slot to receive thumbnail resize events.

        Parameters:
        s (int) - New thumbnail width (in pixels)
        """

        self.in_progress.emit(True)
        if not self.model:
            return

        # update model with new thumbnail scale
        self.model.setThumbnailScale(float(s) / default_thumbnail_resolution)

        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(1)

        self.in_progress.emit(False)

    def setColumnCount(self, n):
        """Does nothing. Included here to be compatible with Designer generated gui"""
        pass

    def setRowCount(self, n):
        """Does nothing. Included here to be compatible with Designer generated gui"""
        pass

    def add_checkpoint(self, msg="", autosave=False, generate_thumbnail=True):
        """Adds document checkpoint to data directory

        Parameters:
            msg (str) - checkpoint message
            autosave (bool) - Save the file first before creating checkpoint
        """

        self.in_progress.emit(True)
        try:
            self.check_has_filename()
            self.check_modified_state(autosave=autosave)
        except CheckFailed as checkfail:
            self.in_progress.emit(False)
            self.report_error(str(checkfail), "Checks failed")
            return

        doc = Krita.instance().activeDocument()

        vmutils = utils.Utils(doc.fileName())
        vmutils.info_update.connect(self.status_update)
        vmutils.error_update.connect(self.report_error)

        # create data directory if this is the first check-point
        if not vmutils.data_dir_exists():
            self.status_update(f"Initializing data directory {vmutils.data_dir}")
            vmutils.init()

        # Create new checkpoint
        doc_id, doc_data = vmutils.add_checkpoint(msg)

        if generate_thumbnail:
            filename = os.path.join(
                vmutils.data_dir, doc_data["dirname"], "thumbnail.png"
            )
            self.status_update(f"Generating thumbnail: {filename}")
            self.generate_thumbnail(doc, filename)
            self.status_update("Updating document history with thumbnail information")
            vmutils.lock_history()
            vmutils.read_history()
            if doc_id not in vmutils.history:
                vmutils.unlock_history()
                self.in_progress.emit(False)
                raise KeyError(f"document {doc_id} not found in history json")
            doc_data = vmutils.history[doc_id]
            doc_data["thumbnail"] = "thumbnail.png"
            vmutils.write_history()
            vmutils.unlock_history()

        self.reload_history()
        self.status_update("Add Checkpoint successfully completed.")

        self.in_progress.emit(False)

    def generate_thumbnail(self, doc, filename):
        """Opens a krita document and generates a new thumbnail images

        Parameters:
            doc (Krita static instance) - document to create clone of
            filename (str) - path to save generated thumbnail to.
        """

        self.in_progress.emit(True)
        clone = doc.clone()
        clone.setBatchmode(True)
        clone.flatten()

        target_dim = float(default_thumbnail_resolution)
        width = clone.width()
        height = clone.height()
        max_dim = max(width, height)
        scale_factor = target_dim / max_dim
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        clone.scaleImage(
            new_width, new_height, clone.resolution(), clone.resolution(), "box"
        )
        self.status_update(f"saving thumbnail to {filename}")
        clone.exportImage(filename, krita.InfoObject())
        clone.close()
        self.in_progress.emit(False)
