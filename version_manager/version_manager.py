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
        print(doc)
        print('---')
        print('"{}"'.format(doc.fileName()))
        print('+++')

        if doc.fileName() == "":
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setText(
                "Please save the current document before creating a checkpoint")
            msgBox.setWindowTitle("Error: File Not Found.")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.exec()
            return

        print(utils)
        vmutils = utils.Utils(doc.fileName(), text_box=self._text_box)
        print('1111')
        print(vmutils.krita_filename)
        # vmutils.init(force=True)
        # vmutils.add_checkpoint('Initial commit')
        print(vmutils.data_dir)
