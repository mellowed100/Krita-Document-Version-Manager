import os
import version_manager.utils as utils
import version_manager.common as common
from pprint import pprint
from PyQt5 import QtCore
from krita import *


def doit():
    print('VersionManager 333333')


class VersionManager(QtCore.QObject):

    progress_update = QtCore.pyqtSignal(int)
    info_update = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def doit(self):
        self.add_checkpoint()

    def add_checkpoint(self, msg='', autosave=False, generate_thumbnail=True):
        """Adds document checkpoint to data directory

        Parameters:
            msg (str) - checkpoint message
            autosave (bool) - Save the file first before creating checkpoint
        """

        doc = Krita.instance().activeDocument()

        # check for new document that hasn't been saved yet
        if doc.fileName() == "":
            common.message_box(
                "No filename found.\nPlease save the current document before creating a checkpoint")
            return

        if doc.modified():
            if autosave:
                self.info_update.emit(
                    'Auto-Save enabled. Saving document to {}'.format(doc.fileName()))
                doc.save()
            else:
                raise Exception(
                    "Document is modified.\nPlease save the current document before creating a checkpoint")

        vmutils = utils.Utils(doc.fileName())

        # create data directory if this is the first check-point
        if not vmutils.data_dir_exists():
            # common.info(f'Initializing data directory {vmutils.data_dir}')
            self.info_update.emit(
                f'Initializing data directory {vmutils.data_dir}')
            vmutils.init()

        doc_id, doc_data = vmutils.add_checkpoint(msg)
        pprint(vmutils.history)

        if generate_thumbnail:
            filename = os.path.join(
                vmutils.data_dir, doc_data['dirname'], 'thumbnail.png')
            self.info_update.emit(f'Generating thumbnail: {filename}')
            self.generate_thumbnail(doc, filename)
            self.info_update.emit(
                'Updating document history with thumbnail information')
            vmutils.lock_history()
            vmutils.read_history()
            history = vmutils.history
            if doc_id not in history:
                vmutils.unlock_history()
                raise KeyError(f'document {doc_id} not found in history json')
            doc_data = history[doc_id]
            doc_data['thumbnail'] = 'thumbnail.png'
            vmutils.write_history()
            vmutils.unlock_history()

    def generate_thumbnail(self, doc, filename):
        clone = doc.clone()
        clone.setBatchmode(True)
        clone.flatten()

        target_dim = 240.0
        width = clone.width()
        height = clone.height()
        max_dim = max(width, height)
        scale_factor = target_dim/max_dim
        clone.scaleImage(int(width*scale_factor), int(height*scale_factor),
                         int(clone.xRes()*scale_factor), int(clone.yRes() * scale_factor), "box")
        info = InfoObject()

        clone.exportImage(filename, info)
