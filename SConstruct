# SPDX-FileCopyrightText: © Cesar Velazquez <cesarve@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
env = Environment()

env['pykrita_dir'] = os.path.join(Path.home(), '.local/share/krita/pykrita')
env['version_manager_dir'] = env['pykrita_dir']+'/version_manager'


##############################
# compile .ui into .py

# build .py from .ui
dep = env.Command('version_manager/qt_docker_widget_ui.py',
                  'version_manager/qt_docker_widget_ui.ui', 'pyuic5 -o $TARGET $SOURCE')

# flag generated python file for deletion
env.Clean(
    dep, 'version_manager/qt_docker_widget_ui.py')

##############################
# compile .qrc into .py

# build .py from .qrc
icon_dep = env.Command('version_manager/icons_rc.py',
                       'version_manager/icons.qrc', 'pyrcc5 -o $TARGET $SOURCE')

# create dependencies of icons.qrc on icon image files
env.Depends('version_manager/icons_rc.py',
            ['version_manager/in_progress.png', 'version_manager/ready.png'])

# flag the generated python file for deletion
env.Clean(icon_dep, 'version_manager/icons_rc.py')


for script in Split("""
__init__.py
utils.py
qt_docker_widget.py
qt_history_widget.py
qt_docker_widget_ui.py
icons_rc.py
"""):
    env.Install(env['version_manager_dir'], f'version_manager/{script}')

env.Install(env['pykrita_dir'], 'version_manager.desktop')

# default build target
env.Default(env['pykrita_dir'])
