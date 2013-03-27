import os
import ConfigParser

from clint import resources

from tenyksclient.meta import meta

client_name = 'tenyksclient'
if hasattr(meta, 'client_name'):
    client_name = meta.client_name

resources.init('Tenyks', client_name)

if os.path.exists(os.path.join(resources.site.path, 'config.ini')):
    config_file = resources.site.open('config.ini', 'r')
else:
    try:
        config_file = resources.user.open('config.ini', 'r')
    except IOError:
        resources.user.write('config.ini', '')
        config_file = resources.user.open('config.ini', 'r')

config = ConfigParser.ConfigParser(allow_no_value=True)
config.readfp(config_file)

if not config.has_section(client_name):
    config.add_section(client_name)

config_defaults = {
    'redis_host': 'localhost',
    'redis_port': '6379',
    'redis_db': 0,
    'redis_password': None,
    'tenyks_broadcast_to': 'tenyks.robot.broadcast_to',
    'client_broadcast_to': 'tenyks.services.broadcast_to',
}


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

modified = False

for key, value in config_defaults.iteritems():
    if not config.has_option(client_name, key):
        modified = True
        config.set(client_name, key, value)
        setattr(settings, key, value)
    else:
        new_value = config.get(client_name, key)
        setattr(settings, key, new_value)

for option in config.options(client_name):
    if not option in config_defaults:
        setattr(settings, option, config.get(client_name, option))


if modified:
    config_file = resources.user.open('config.ini', 'w')
    config.write(config_file)
    #resources.user.close('config.ini')
