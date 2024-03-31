from PyQt5 import QtWidgets
import version_manager.utils as utils
import version_manager.common as common


def doit():
    print('VersionManager 333333')


class VersionManager(object):

    def __init__(self, text_box=None):
        pass
        self._text_box = text_box
        common.status_bar = self._text_box

    def doit(self):
        self.add_checkpoint()

    def add_checkpoint(self):
        print('ccccc')

        doc = Krita.instance().activeDocument()

        # check if document saved to disk
        if doc.fileName() == "":
            common.message_box(
                "Please save the current document before creating a checkpoint")
            return

        print(utils)
        vmutils = utils.Utils(doc.fileName(), text_box=self._text_box)
        print('1111')
        print(vmutils.krita_filename)
        if not vmutils.data_dir_exists():
            # common.message_box('Please initialize before adding checkpoints')
            common.info(f'Initializing data directory {vmutils.data_dir}')
            vmutils.init()

        vmutils.add_checkpoint('Initial commit')
        print(vmutils.data_dir)
