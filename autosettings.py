import os
import sys
import re
import dj_database_url
import urlparse
import importlib

noprefix_keys = [
            'DEBUG', 
            'PROJECT_NAME',
            'BASE_DIR',
            'DATABASE_URL',
            'MEMCACHED_URL',
        ]

def plugin_django(env, settings):
    for k,v in env.items():
        key = None

        if k in noprefix_keys:
            key = k
        elif k.startswith('DJANGO_'):
            key = k[7:]

        if key:
            if v in ['True', 'False']: 
                v = (v == 'True')
            elif v.isdigit(): 
                v = int(v)

            settings[key] = v

def plugin_database(env, settings):
    url = env.get('DATABASE_URL', None)
    if not url: return

    settings['DATABASES'] = {'default': dj_database_url.parse(url)} 

def plugin_memcached(env, settings):
    url = env.get('MEMCACHED_URL', None)
    if not url: return

    url = urlparse.urlparse(url)

    host = url.hostname 
    port = url.port

    settings.update({
        'CACHES': {
            'default': {
                'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',    
                'LOCATION': '{0}:{1}'.format(host, port),    
            }        
        }
    })

def discover_projectroot(test_calling=None):
    frame = sys._getframe()
    while os.path.basename(frame.f_code.co_filename) == 'autosettings.py':
        frame = frame.f_back
    calling_file = frame.f_code.co_filename
    projectroot = os.path.dirname(calling_file)
    calling_file = os.path.basename(calling_file)

    if calling_file == 'tests.py' and test_calling:
        calling_file = test_calling
        
    if calling_file == 'wsgi.py':
        projectroot = os.path.join(projectroot, '..') 

    projectroot = os.path.abspath(projectroot)
    if os.path.exists(projectroot):
        return projectroot
    else:
        return None

def readenvfromfile(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        f.close()

    env = {}
    for line in lines:
        match = re.match('^([A-Z_]+)=(.*)$', line)
        if match:
            k = match.group(1)
            if k not in noprefix_keys:
                k = 'DJANGO_' + k
    
            env[k] = match.group(2)

    return env

def getenv(envpath=None, include_environ=True):
    if envpath and os.path.isdir(envpath):
        envpath = os.path.join(envpath, '.env')

    if include_environ:
        env = dict(os.environ)
    else:
        env = {}

    if envpath and os.path.isfile(envpath): 
        env.update(readenvfromfile(envpath))

    return env

def get_django_settings(modulename, settings):
    """
    modulename = modulename.split('.')
    if len(modulename) == 1:
        settings_module = __import__(modulename[0])
    else:
        last = modulename.pop()
        _temp = __import__('.'.join(modulename), fromlist=[last])
        settings_module = _temp.__dict__[last]
    """
    projectroot = settings['BASE_DIR']
    modulepath = os.path.join(*modulename.split('.')) + '.py'
    modulefile = os.path.join(settings['BASE_DIR'], modulepath)
    with open(modulefile, 'r') as f:
        modulecode = f.read()
        f.close()

    exec_settings = settings.copy()
    exec modulecode in {}, exec_settings

    for k,v in exec_settings.items():
        if k.isupper():
            settings[k] = v

def config(projectroot=None, settings_func=None):
    if config.loaded: return

    if not projectroot:
        projectroot = discover_projectroot()

    env = getenv(projectroot)
    settings = {
        'BASE_DIR': projectroot        
    }
    
    for method in dir(sys.modules[__name__]):
        if method.startswith('plugin_'):
            globals()[method](env, settings)

    projectname = settings.get('PROJECT_NAME', None)
    if projectname:
        modulename = projectname+'.settings'
        get_django_settings(modulename, settings)

    if not settings_func:
        import django.conf
        settings_func = django.conf.settings.configure
    
    settings_func(**settings)
    config.loaded = True

    return projectroot, env, settings
config.loaded = False
