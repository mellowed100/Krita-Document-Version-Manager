import sys
from importlib import reload


def doit():

    for item in sys.path:
        print(item)

    try:
        import version_manager
    except:
        if 'version_manager' in sys.modules:
            print('Reload version_manager')
            reload(sys.modules['version_manager'])
    # reload(version_manager).version_manager
