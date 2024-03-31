import version_manager.utils as utils
import version_manager.common as common
from pprint import pprint


def doit():
    print('VersionManager 333333')


class VersionManager(object):

    def __init__(self, text_box=None):
        pass
        self._text_box = text_box
        common.status_bar = self._text_box

    def doit(self):
        self.add_checkpoint()

    def add_checkpoint(self, msg='', autosave=False):
        """Adds document checkpoint to data directory

        Parameters:
            msg (str) - checkpoint message
            autosave (bool) - Save the file first before creating checkpoint
        """
        print('11111')
        print(autosave)
        print(msg)

        doc = Krita.instance().activeDocument()

        # check for new document that hasn't been saved yet
        if doc.fileName() == "":
            common.message_box(
                "No filename found.\nPlease save the current document before creating a checkpoint")
            return

        if doc.modified():
            if autosave:
                pass
                common.info('Saving document to {}'.format(doc.fileName()))
                doc.save()
            else:
                common.message_box(
                    "Document is modified.\nPlease save the current document before creating a checkpoint")
                return

        vmutils = utils.Utils(doc.fileName(), text_box=self._text_box)

        # create data directory if this is the first check-point
        if not vmutils.data_dir_exists():
            common.info(f'Initializing data directory {vmutils.data_dir}')
            vmutils.init()

        vmutils.add_checkpoint(msg)
        pprint(vmutils.history)
