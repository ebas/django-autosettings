from autosettings import *
from nose.tools import *
import tempfile
import shutil

class TestAutosettings(object):
    TEST_ENV = {'DEBUG':'True','PROJECT_NAME':'FOO'}

    def setup(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.tmpdir)

    def mkenvfile(self, value, path='.'):
        if type(value) == dict:
            txt = '\n'.join(['{0}={1}'.format(k,v) for k,v in value.items()])

        path = os.path.join(self.tmpdir, path, '.env')

        with open(path, 'w') as f:
            f.write(txt)
            f.close()
        
    def test_discover_projectroot(self):
        check_dir = os.path.dirname(__file__)
        eq_(check_dir, discover_projectroot('manage.py'))

        check_dir = os.path.abspath(os.path.join(check_dir, '..'))
        eq_(check_dir, discover_projectroot('wsgi.py'))

    def test_getenv(self):
        eq_(os.environ, getenv())

        self.mkenvfile(self.TEST_ENV)
        eq_(self.TEST_ENV, getenv(self.tmpdir, include_environ=False))
        eq_(self.TEST_ENV, getenv(os.path.join(self.tmpdir, '.env'), include_environ=False))
        
    def test_get_django_settings(self):
        settings = {'BASE_DIR': self.tmpdir}

        sys.path.insert(0, self.tmpdir)
        with open(os.path.join(self.tmpdir, 'settings.py'), 'w') as f:
            f.write('\n'.join([
                'TEST=123',
                'DIR=BASE_DIR']))
            f.close()

        get_django_settings('settings', settings)

        eq_(settings, {
            'TEST': 123,
            'DIR': self.tmpdir,
            'BASE_DIR': self.tmpdir,
        })

    def test_config(self):
        def settings_func(**kwargs):
            settings_func.called = kwargs 

        projectname = 'testproject'
        os.environ['PROJECT_NAME'] = projectname

        sys.path.insert(0, self.tmpdir)
        path = os.path.join(self.tmpdir, projectname) 
        os.makedirs(path)
        with open(os.path.join(path, '__init__.py'), 'w') as f:
            f.close()

        with open(os.path.join(path, 'settings.py'), 'w') as f:
            f.write('TEST=123')
            f.close()

        settings_func.called = None
        config(self.tmpdir, settings_func)
        eq_(settings_func.called, {
            'TEST': 123,
            'PROJECT_NAME': projectname,
            'BASE_DIR': self.tmpdir
        })

    def test_plugin_django(self):
        env = {
            'FOO': 'BAR',
            'DJANGO_SECRET_KEY': 'Test',
            'DEBUG': 'False',
        }

        settings = {}
        plugin_django(env, settings)

        eq_(settings, {
            'SECRET_KEY': 'Test',
            'DEBUG': False
        })

    def test_plugin_database(self):
        env = {
            'DATABASE_URL': 'mysql://user:pass@host:3306/database',
        }

        settings = {}
        plugin_database(env, settings)

        eq_(settings, {
            'DATABASES': {
                'default': {
                    'ENGINE': 'django.db.backends.mysql', 
                    'NAME': 'database', 
                    'HOST': 'host', 
                    'USER': 'user', 
                    'PASSWORD': 'pass', 
                    'PORT': 3306
                }
            }
        })

    def test_plugin_memcached(self):
        env = {
            'MEMCACHED_URL': 'memcached://host:11211',
        }

        settings = {}
        plugin_memcached(env, settings)

        eq_(settings, {
            'CACHES': {
                'default': {
                    'LOCATION': 'host:11211', 
                    'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache'
                }
            }
        })
