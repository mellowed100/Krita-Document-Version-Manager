import os
from pathlib import Path
env = Environment()

env['pykrita_dir'] = os.path.join(Path.home(), '.local/share/krita/pykrita')
env['version_manager_dir'] = env['pykrita_dir']+'/version_manager'

for script in Split("""
__init__.py
utils.py
portalocker.py
qt_docker_widget.py
qt_history_widget.py
"""):
    env.Install(env['version_manager_dir'], f'version_manager/{script}')

env.Install(env['pykrita_dir'], 'version_manager.desktop')

# default build target
env.Default(env['pykrita_dir'])

##############################
# compile .ui into .py
guis = """
qt_docker_widget_ui
            """.split()

for gui in guis:
    target = '{tgt}/{gui}.py'.format(tgt=env['version_manager_dir'], gui=gui)
    source = 'version_manager/{gui}.ui'.format(gui=gui)

    # build .py from .ui
    dep = env.Command(target, source, 'pyuic5 -o $TARGET $SOURCE')

    # flag generated python file for deletion
    env.Clean(
        dep, '{tgt}/{gui}.py'.format(tgt=env['version_manager_dir'], gui=gui))
