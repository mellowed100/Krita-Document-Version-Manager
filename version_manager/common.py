from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import threading
import sys
import subprocess
import logging
import os
import datetime
import platform

use_gui = False

try:
    import krita
    from PyQt5 import QtWidgets
    use_gui = True
except:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Krita Version Manager')

verbose_4 = 6  # max verbose
verbose_3 = 7
verbose_2 = 8
verbose_1 = 9  # min verbose

logging.addLevelName(verbose_4, "verbose_4")
logging.addLevelName(verbose_3, "verbose_3")
logging.addLevelName(verbose_2, "verbose_2")
logging.addLevelName(verbose_1, "verbose_1")

status_bar = None


def set_logging_level(level):
    logger.setLevel(level)


def now():
    return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')


def info(rMsg):
    if status_bar:
        status_bar.append('Info: {}'.format(rMsg))
        return

    logger.info('{} - {}'.format(now(), rMsg))
    sys.stdout.flush()


def debug(rMsg):
    if status_bar:
        status_bar.append('Debug: {}'.format(rMsg))
        return

    logger.debug('{} - {}'.format(now(), rMsg))
    sys.stdout.flush()


def error(rMsg):
    if status_bar:
        status_bar.append('Error: {}'.format(rMsg))
        return
    logger.error('{} - {}'.format(now(), rMsg))
    raise Exception(rMsg)


def warn(rMsg):
    if status_bar:
        status_bar.append('Warn: {}'.format(rMsg))
        return
    logger.warning('{} - {}'.format(now(), rMsg))


def verbose(rLevel, rMsg):
    if logger.level > rLevel:
        return

    if status_bar:
        status_bar.append(rMsg)
        return

    logger.info('{} - {}'.format(now(), rMsg))


class streamPipe(threading.Thread):
    """
    Read data from rInput.
    Data read from rInput is appended to self.mOutput
    """

    def __init__(self, rInput, rOutput=sys.stderr, rOutputName="STDERR=> "):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._Input = rInput
        self._StoreInput = []
        self._Output = rOutput
        self._OutputName = rOutputName

    def run(self):
        while True:
            s = self._Input.readline()
            if s == "":
                return

            if self._Output:
                self._Output.write(s.decode('utf-8'))
            self._StoreInput.append(s.decode('utf-8'))


def runCommand(rCmd):
    """Run a shell command

    Parameters:
        rCmd (str): Shell command to run

    Returns:
        return code from shell command
    """

    debug(rCmd)

    # create process to execute command
    proc = subprocess.Popen(rCmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)

    # create new thread to read stdout
    stdoutlog = streamPipe(proc.stdout, sys.stdout, "STDOUT=> ")
    stdoutlog.start()

    # create new thread to read stderr
    stderrlog = streamPipe(proc.stderr, sys.stderr, "STDERR=> ")
    stderrlog.start()

    # wait for job to finish. Get return code
    returnCode = proc.wait()

    return returnCode


def dirIsEmpty(rPath):
    """Check if a directory is empty"""

    if os.path.isdir(rPath):
        return False

    if len(os.listdir(rPath)):
        return False

    return True


def creation_date(path_to_file):
    """
    From https://stackoverflow.com/questions/237079/how-do-i-get-file-creation-and-modification-date-times
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            print('bbbb')
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            print('aaaaa')
            return stat.st_mtime
