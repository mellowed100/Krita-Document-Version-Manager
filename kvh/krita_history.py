from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import json
import datetime
import time
from . import common


class KritaVersionHistory(object):
    # history_dict = {'documents': {}}
    history_dict = {}
    document_dict = {'filename': '', 'thumbnail': '',
                     'modtime': 0., 'dirname': ''}

    def __init__(self, filename):
        self._krita_file = filename

        if not os.path.exists(self.krita_filename):
            common.error(f'File not found: {self.krita_filename}')

        self._krita_file = os.path.abspath(self.krita_filename)

        krita_path, self._krita_basename = os.path.split(self.krita_filename)
        self._version_directory = os.path.join(
            krita_path, '.{}'.format(self.krita_basename))

        self._data_filename = os.path.join(self.data_dir, 'history.json')

        self._history = None

    @property
    def krita_filename(self):
        """Absolute path to source krita document"""
        return self._krita_file

    @property
    def krita_basename(self):
        """Document basename"""
        return self._krita_basename

    @property
    def data_dir(self):
        """Absolute path to data directory"""
        return self._version_directory

    @property
    def history_filename(self):
        """Absolute path to history json file"""
        return self._data_filename

    @property
    def history(self):
        """Dictionary holding history data"""
        return self._history

    def init(self, force=False):
        """Create and initialize data directory"""

        if os.path.exists(self.data_dir) and force:
            shutil.rmtree(self.data_dir)

        if os.path.exists(self.data_dir):
            common.error(
                f'Cannot initialize data directory. Directory already exists: {self.data_dir}')

        os.makedirs(self.data_dir)

        self._history = KritaVersionHistory.history_dict.copy()

        self.write_history()

    def write_history(self):
        """Writes document history to json"""

        with open(self.history_filename, 'w') as file_out:
            json.dump(self.history, file_out, sort_keys=True, indent=4)

    def read_history(self):
        """Loads document history from disk"""

        if not os.path.exists(self.history_filename):
            common.error(f'File not found: {self.history_filename}')
            self._history = None
            return

        with open(self.history_filename, 'r') as file_in:
            self._history = json.load(file_in)

    def connect(self):
        """Initialize connection to document history"""

        self.read_history()

    def add_checkpoint(self):
        """Adds a new checkpoint for the krita document.

            This will store a copy of the krita file as well as
            a thumbnail and checkpoint metadata. """

        if not os.path.exists(self.krita_filename):
            common.error(f'File not found: {self.krita_filename}')
            return

        modtime = common.creation_date(self.krita_filename)
        dirname = 'doc_{}'.format(str(modtime).replace('.', '_'))

        print(time.strftime('%Y-%m%d %H:%M:%S', time.localtime(modtime)))
        doc_dir = os.path.join(self.data_dir, dirname)

        # quit if an entry for this timestamp already exists
        if dirname in self.history:
            common.error(
                'Timestamp for this version of the krita file already exists')
            return

        # quit if a document directory for this timestamp already exists
        if os.path.exists(doc_dir):
            common.error(
                f'Document directory already exists: {doc_dir}')
            return

        self.history[modtime] = KritaVersionHistory.document_dict.copy()

        doc_data = self.history[modtime]
        doc_data['modtime'] = modtime
        doc_data['filename'] = self.krita_basename
        doc_data['dirname'] = dirname

        os.makedirs(doc_dir)

        shutil.copyfile(self.krita_filename, os.path.join(
            doc_dir, self.krita_basename))

        self.write_history()
