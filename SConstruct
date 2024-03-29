env = Environment()

env['pykrita_dir'] = '/home/cesar/.local/share/krita/pykrita'
env['version_manager_dir'] = env['pykrita_dir']+'/version_manager'

for script in Split("""
__init__.py
common.py
utils.py
version_manager.py
"""):
    env.Install(env['version_manager_dir'], f'version_manager/{script}')

env.Install(env['pykrita_dir'], 'version_manager.desktop')
env.Install(env['pykrita_dir'], 'version_manager_reload.py')

# default build target
env.Default(env['pykrita_dir'])
