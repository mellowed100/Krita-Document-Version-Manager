
from krita import DockWidget
from PyQt5 import QtWidgets

from .utils import Utils
import version_manager.utils as utils
import version_manager.version_manager as VM
import version_manager.main_window_ui

'''
from importlib import reload
import version_manager.version_manager as vm
reload(vm)
vm.foo()



import sys
from importlib import reload

for item in sys.modules:
    print(item)

reload(sys.modules['version_manager.version_manager'])


import sys
from importlib import reload

for item in sys.modules:
    print(item)

import version_manager.utils
reload(version_manager.utils)

version_manager.utils.doit()

'''


class VersionManagerGui(DockWidget, main_window_ui):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Version Manager")

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        doit_button = QtWidgets.QPushButton(text='doit')
        doit_button.clicked.connect(self.doit)
        layout.addWidget(doit_button)

        reload_button = QtWidgets.QPushButton(text='reload modules')
        reload_button.clicked.connect(self.reload_modules)
        layout.addWidget(reload_button)

        self.textbox = QtWidgets.QTextEdit()
        self.textbox.setReadOnly(True)
        layout.addWidget(self.textbox)

        self.setWidget(widget)

    def doit(self, s):
        print(s)
        from importlib import reload
        reload(VM)
        vm = VM.VersionManager(self.textbox)
        vm.doit()

    def reload_modules(self):
        from importlib import reload

        import version_manager.utils
        reload(version_manager.utils)
        version_manager.utils.doit()

        import version_manager.version_manager
        reload(version_manager.version_manager)
        version_manager.version_manager.doit()

    def canvasChanged(self, canvas):
        pass
