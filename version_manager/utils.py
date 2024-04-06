# SPDX-FileCopyrightText: © Cesar Velazquez <cesarve@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import platform
import errno
import shutil
import json
from datetime import datetime
from pwd import getpwuid
from PyQt5 import QtCore
from . import portalocker


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

        super().__init__()

        self._krita_file = filename

        # check source krita document
        if not os.path.exists(self.krita_filename):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.krita_filename)

        # get absolute path to krita document
        self._krita_file = os.path.abspath(self.krita_filename)

        self._krita_path, self._krita_basename = os.path.split(
            self.krita_filename)

        # set path to document data directory
        self._version_directory = os.path.join(
            self.krita_dir, '{}.d'.format(self.krita_basename))

        self._data_basename = 'history.json'
        self._data_filename = os.path.join(self.data_dir, self._data_basename)

        # dictionary holding  ndata for all document versions
        self._history = None

        # lockfile used when writing history json file
        self._lockfile = None

    @property
    def krita_filename(self):
        """Absolute path to source krita document"""
        return self._krita_file

    @property
    def krita_dir(self):
        """Directory containing krita document"""
        return self._krita_path

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

    def history_exists(self):
        """Returns True if history file exists"""
        return os.path.exists(self.history_filename)

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

    def lock_history(self):
        """Locks history json file"""

        lock_filename = os.path.join(
            self.data_dir, f'{self.history_basename}.lock')

        self._lockfile = open(lock_filename, 'w')

        # use lockfile as a proxy for history.json
        portalocker.lock(self._lockfile, portalocker.LOCK_EX)

    def unlock_history(self):
        """Unlock history json file"""
        portalocker.unlock(self._lockfile)
        self._lockfile.close()
        self._lockfile = None

    def update_checkpoint_message(self, doc_id, msg):
        """Updates the check-in message for a document

        Parameters:
        doc_id (str): history dictionary key of the document to update
        msg (str): new message to update document checkpoint with.
        """

        self.lock_history()
        self.read_history()
        if doc_id not in self.history:
            raise IndexError(f'unknown document index {doc_id}')
        self.history[doc_id]['message'] = repr(msg)
        self.write_history()
        self.unlock_history()

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

        # more human readable form for displaying in history widget.
        date = datetime.fromtimestamp(modtime).strftime(
            '%m/%d/%Y\n%I:%M %p\n%A')

        # name of directory to hold checkpoint data
        dirname = datetime.fromtimestamp(
            modtime).strftime('doc__%Y_%m_%d__%H_%M_%S_%f')
        doc_dir = os.path.join(self.data_dir, dirname)

        self.lock_history()
        self.read_history()

        # quit if an entry for this timestamp already exists
        if dirname in self.history:
            self.unlock_history()
            raise Exception(
                'Timestamp for this version of the krita file already exists')

        # quit if a document directory for this timestamp already exists
        if os.path.exists(doc_dir):
            self.unlock_history()
            raise FileExistsError(
                f'No modifications to save. A checkpoint for this timestamp already exists. {date}')

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

        # make document data directory
        os.makedirs(doc_dir)

        # copy krita file to document data directory
        shutil.copyfile(self.krita_filename, os.path.join(
            doc_dir, self.krita_basename))

        self.write_history()
        self.unlock_history()

        return doc_id, self.history[doc_id]
