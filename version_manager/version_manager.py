import version_manager.utils as utils


def doit():
    print('VersionManager 333333')


class VersionManager(object):

    def __init__(self):
        pass

    def doit(self):
        print('ccccc')

        doc = Krita.instance().activeDocument()
        print(doc)
        print(doc.fileName())

        print(utils)
        vmutils = utils.Utils(doc.fileName())
        print('1111')
        print(vmutils.krita_filename)
        vmutils.init(force=True)
        vmutils.add_checkpoint('Initial commit')
