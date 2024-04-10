import os

"""
 https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s25.html   
"""

if os.name == 'nt':
    # Hiding this section because the windows version of Krita
    # doesn't include these modules with its version of python.

    # import win32con
    # import win32file
    # import pywintypes
    # LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    # LOCK_SH = 0  # the default
    # LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    # __overlapped = pywintypes.OVERLAPPED()

    # def lock(file, flags):
    #     hfile = win32file._get_osfhandle(file.fileno())
    #     win32file.LockFileEx(hfile, flags, 0, 0xffff0000, __overlapped)

    # def unlock(file):
    #     hfile = win32file._get_osfhandle(file.fileno())
    #     win32file.UnlockFileEx(hfile, 0, 0xffff0000, __overlapped)

    LOCK_EX = 0
    LOCK_SH = 0
    LOCK_NB = 0

    def lock(file, flags):
        pass

    def unlock(file):
        pass
elif os.name == 'posix':
    import fcntl
    from fcntl import LOCK_EX, LOCK_SH, LOCK_NB

    def lock(file, flags=fcntl.LOCK_EX):
        fcntl.flock(file.fileno(), flags)

    def unlock(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)
else:
    raise RuntimeError("PortaLocker only defined for nt and posix platforms")
