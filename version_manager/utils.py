from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import errno
import shutil
import json
import time
from pwd import getpwuid

try:
    import krita
    from . import portalocker
    from . import common
except ImportError:
    import portalocker
    import common


def doit():
    print('Utils - 222222')


class Utils(object):
    """Manages lower level operations for Krita document version manager"""

    history_template = {}
    document_template = {'filename': '', 'thumbnail': '',
                         'modtime': 0., 'dirname': '', 'message': '',
                         'owner': ''}

    def __init__(self, filename, text_box=None):
        """

        Arguments:
        filename (str) - Krita document .kra to manage
        """
        if text_box:
            common.status_bar = text_box

        self._krita_file = filename

        # check source krita document
        if not os.path.exists(self.krita_filename):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.krita_filename)

        # get absolute path to krita document
        self._krita_file = os.path.abspath(self.krita_filename)

        krita_path, self._krita_basename = os.path.split(self.krita_filename)

        # set path to document data directory
        self._version_directory = os.path.join(
            krita_path, '.{}'.format(self.krita_basename))

        self._data_basename = 'history.json'
        self._data_filename = os.path.join(self.data_dir, self._data_basename)

        # dictionary holding data for all document versions
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
    def history_basename(self):
        """Absolute path to history json file"""
        return self._data_basename

    @property
    def history(self):
        """Dictionary holding history data"""
        return self._history

    def data_dir_exists():
        """Returns True if data_dir exists"""
        return os.path.exists(self.data_dir)

    def init(self, force=False):
        """Create and initialize data directory"""

        if self.data_dir_exists():
            if force:
                shutil.rmtree(self.data_dir)
            else:
                common.error(
                    f'Cannot initialize data directory. Directory already exists: {self.data_dir}')

        os.makedirs(self.data_dir)

        self._history = Utils.history_template.copy()

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

    def add_checkpoint(self, msg=''):
        """Adds a new checkpoint for the krita document.

            This will store a copy of the krita file as well as
            a thumbnail and checkpoint metadata.


            Arguments:
            msg - str: Checkpoint message
            """

        # check that krita file exists
        if not os.path.exists(self.krita_filename):
            common.error(f'File not found: {self.krita_filename}')
            return

        # get modification time of krita file
        modtime = common.creation_date(self.krita_filename)
        dirname = 'doc_{}'.format(str(modtime).replace('.', '_'))

        # name of directory to hold checkpoint data
        doc_dir = os.path.join(self.data_dir, dirname)

        self.read_history()

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

        # lock history json file
        lock_filename = os.path.join(
            self.data_dir, f'.{self.history_basename}.lock')

        # with FileLock(lock_filename, timeout=5):
        with open(lock_filename, 'w') as lockfile:

            # use lockfile as a proxy for history.json
            portalocker.lock(lockfile, portalocker.LOCK_EX)

            # self.read_history()

            # create copy of document dictionary template
            self.history[modtime] = Utils.document_template.copy()

            for key, value in (('modtime', modtime),
                               ('filename', self.krita_basename),
                               ('dirname', dirname),
                               ('message', repr(msg)),
                               ('author', getpwuid(os.stat(self.krita_filename).st_uid).pw_name)):
                self.history[modtime][key] = value

            os.makedirs(doc_dir)

            shutil.copyfile(self.krita_filename, os.path.join(
                doc_dir, self.krita_basename))

            self.write_history()

            portalocker.unlock(lockfile)
