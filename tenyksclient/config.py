import os
from os.path import abspath, join, dirname
import sys
import logging.config

from tenyksclient.module_loader import make_module_from_file


PROJECT_ROOT = abspath(dirname(__file__))


class NotConfigured(Exception):
    pass


# taken from legit (https://github.com/kennethreitz/legit)
class Settings(object):
    _singleton = {}

    # attributes with defaults
    __attrs__ = tuple()

    def __init__(self, **kwargs):
        super(Settings, self).__init__()

        self.__dict__ = self._singleton

    def __call__(self, *args, **kwargs):
        # new instance of class to call
        r = self.__class__()

        # cache previous settings for __exit__
        r.__cache = self.__dict__.copy()
        map(self.__cache.setdefault, self.__attrs__)

        # set new settings
        self.__dict__.update(*args, **kwargs)

        return r

    def __enter__(self):
        pass

    def __exit__(self, *args):
        # restore cached copy
        self.__dict__.update(self.__cache.copy())
        del self.__cache

    def __getattribute__(self, key):
        if key in object.__getattribute__(self, '__attrs__'):
            try:
                return object.__getattribute__(self, key)
            except AttributeError:
                return None
        return object.__getattribute__(self, key)


settings = Settings()

def collect_settings(settings_path=None, client_name=None):
    intrl_settings = None
    if not len(sys.argv) > 1:
        message = """
You need to provide a settings module.

Use `tenyksclientmkconfig > /path/to/settings.py`
        """.format(pr=PROJECT_ROOT)
        raise NotConfigured(message)
    intrl_settings = make_module_from_file('settings', sys.argv[1])

    if client_name and not getattr(settings, 'CLIENT_NAME', None):
        setattr(settings, 'CLIENT_NAME', client_name)

    for sett in filter(lambda x: not x.startswith('__'), dir(intrl_settings)):
        setattr(settings, sett, getattr(intrl_settings, sett))

    if not hasattr(intrl_settings, 'WORKING_DIR'):
        WORKING_DIR = getattr(intrl_settings, 'WORKING_DIRECTORY_PATH',
                join(os.environ['HOME'], '.config', settings.CLIENT_NAME))
        setattr(settings, 'WORKING_DIR', WORKING_DIR)

    if not hasattr(intrl_settings, 'LOGGING_CONFIG'):
        intrl_settings.LOGGING_CONFIG = LOGGING_CONFIG = {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'color': {
                    'class': 'tenyks.logs.ColorFormatter',
                    'format': '%(asctime)s %(name)s:%(levelname)s %(message)s'
                },
                'default': {
                    'format': '%(asctime)s %(name)s:%(levelname)s %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'color'
                },
                'file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'formatter': 'default',
                    'filename': join(WORKING_DIR, 'tenyks.log')
                }
            },
            'loggers': {
                settings.CLIENT_NAME: {
                    'handlers': ['console'],
                    'level': ('DEBUG' if settings.DEBUG else 'INFO'),
                    'propagate': True
                },
            }
        }

    setattr(settings, 'LOGGING_CONFIG', intrl_settings.LOGGING_CONFIG)

    logging.config.dictConfig(LOGGING_CONFIG)

def make_config():
    with open(join(PROJECT_ROOT, 'settings.py.dist'), 'r') as f:
        for line in f.readlines():
            print line,
