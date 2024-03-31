from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import platform
import errno
import shutil
import time
import json
import krita
from pwd import getpwuid
from PyQt5 import QtCore
from . import portalocker


def doit():
    print('Utils - 222222')


def creation_date(path_to_file):
    """
    From https://stackoverflow.com/questions/237079/how-do-i-get-file-creation-and-modification-date-times
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


class Utils(QtCore.QObject):
    """Manages lower level operations for Krita document version manager"""

    history_template = {}
    document_template = {'filename': '', 'thumbnail': '',
                         'mtime': 0., 'dirname': '', 'message': '',
                         'owner': '', 'date': ''}

    def __init__(self, filename):
        """

        Arguments:
        filename (str) - Krita document .kra to manage
        """

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

    def data_dir_exists(self):
        """Returns True if data_dir exists"""
        return os.path.exists(self.data_dir)

    def init(self, force=False):
        """Create and initialize data directory


        Raises FileExistsError if the data directory exists already
        """

        if self.data_dir_exists():
            if force:
                shutil.rmtree(self.data_dir)
            else:
                raise FileExistsError(
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
            raise FileNotFoundError(f'File not found: {self.history_filename}')

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
            raise FileNotFoundError(f'File not found: {self.krita_filename}')

        # get modification time of krita file
        modtime = creation_date(self.krita_filename)
        dirname = 'doc_{}'.format(str(modtime).replace('.', '_'))

        date = time.strftime('%a, %B %e, %Y - %I:%M %p',
                             time.localtime(modtime))

        # name of directory to hold checkpoint data
        doc_dir = os.path.join(self.data_dir, dirname)

        self.read_history()

        # quit if an entry for this timestamp already exists
        if dirname in self.history:
            raise Exception(
                'Timestamp for this version of the krita file already exists')

        # quit if a document directory for this timestamp already exists
        if os.path.exists(doc_dir):
            raise FileExistsError(
                f'No modifications to save. A checkpoint for this timestamp already exists. {date}')

        # lock history json file
        lock_filename = os.path.join(
            self.data_dir, f'.{self.history_basename}.lock')

        # with FileLock(lock_filename, timeout=5):
        with open(lock_filename, 'w') as lockfile:

            # use lockfile as a proxy for history.json
            portalocker.lock(lockfile, portalocker.LOCK_EX)

            # self.read_history()

            doc_id = str(modtime)
            # create copy of document dictionary template
            self.history[doc_id] = Utils.document_template.copy()

            for key, value in (('mtime', modtime),
                               ('filename', self.krita_basename),
                               ('dirname', dirname),
                               ('message', repr(msg)),
                               ('date', date),
                               ('owner', getpwuid(os.stat(self.krita_filename).st_uid).pw_name)):
                self.history[doc_id][key] = value

            os.makedirs(doc_dir)

            shutil.copyfile(self.krita_filename, os.path.join(
                doc_dir, self.krita_basename))

            self.write_history()

            portalocker.unlock(lockfile)
