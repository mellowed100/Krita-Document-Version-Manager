env = Environment()

env['pykrita_dir'] = '/home/cesar/.local/share/krita/pykrita'
env['kritagit_dir'] = env['pykrita_dir']+'/kritagit'

for script in Split("""
kritagit/__init__.py
kritagit/repo.py
kritagit/kritagit.py
"""):
    env.Install(env['kritagit_dir'], script)

env.Install(env['pykrita_dir'], 'kritagit.desktop')
env.Install(env['pykrita_dir'], 'kritagit_reload.py')

# default build target
env.Default(env['pykrita_dir'])
