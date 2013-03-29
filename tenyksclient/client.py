import gevent.monkey
gevent.monkey.patch_all()

import json
import re

import gevent
import redis

import logging

from tenyksclient.config import settings


CLIENT_SERVICE_STATUS_OFFLINE = 0
CLIENT_SERVICE_STATUS_ONLINE = 1


class Client(object):

    irc_message_filters = {}
    name = None
    direct_only = False

    def __init__(self):
        self.channels = [settings.client_broadcast_to]
        if self.name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = self.name.lower()
        if self.irc_message_filters:
            self.re_irc_message_filters = {}
            for name, regexes in self.irc_message_filters.iteritems():
                if not name in self.re_irc_message_filters:
                    self.re_irc_message_filters[name] = []
                if isinstance(regexes, basestring):
                    regexes = [regexes]
                for regex in regexes:
                    self.re_irc_message_filters[name].append(
                        re.compile(regex).match)
        if hasattr(self, 'recurring'):
            gevent.spawn(self.run_recurring)
        self.logger = logging.getLogger(self.name)

    def run_recurring(self):
        self.recurring()
        recurring_delay = getattr(self, 'recurring_delay', 30)
        gevent.spawn_later(recurring_delay, self.run_recurring)

    def run(self):
        r = redis.Redis(host=settings.redis_host,
                        port=int(settings.redis_port),
                        db=settings.redis_db,
                        password=settings.redis_password)
        pubsub = r.pubsub()
        pubsub.subscribe(self.channels)
        for raw_redis_message in pubsub.listen():
            try:
                if raw_redis_message['data'] != 1L:
                    data = json.loads(raw_redis_message['data'])
                    if self.direct_only and not data['direct']:
                        continue
                    if self.irc_message_filters:
                        name, match = self.search_for_match(data['payload'])
                        if match:
                            self.delegate_to_handle_method(data, match, name)
                    else:
                        gevent.spawn(self.handle, data, None, None)
            except ValueError:
                self.logger.info('Invalid JSON. Ignoring message.')

    def search_for_match(self, message):
        for name, regexes in self.re_irc_message_filters.iteritems():
            for regex in regexes:
                match = regex(message)
                if match:
                    return name, match
        return None, None

    def delegate_to_handle_method(self, data, match, name):
        if hasattr(self, 'handle_{name}'.format(name=name)):
            callee = getattr(self, 'handle_{name}'.format(name=name))
            gevent.spawn(callee, data, match)
        else:
            gevent.spawn(self.handle, data, match, name)

    def handle(self, data, match, filter_name):
        raise NotImplementedError('`handle` needs to be implemented on all '
                                  'Client subclasses.')

    def send(self, message, data=None):
        r = redis.Redis(host=settings.redis_host,
                        port=int(settings.redis_port),
                        db=settings.redis_db,
                        password=settings.redis_password)
        broadcast_channel = settings.tenyks_broadcast_to
        if data:
            to_publish = json.dumps({
                'command': data['command'],
                'client': self.name,
                'payload': message,
                'target': data['target'],
                'connection': data['connection']
            })
        r.publish(broadcast_channel, to_publish)


class WebServiceClient(Client):

    def __init__(self):
        super(WebServiceClient, self).__init__()
        self.channels.append('tenyks.services.from_ws')

    def web_handle(self, data, match, filter_name):
        raise NotImplementedError('`handle` needs to be implemented on all '
                                  'Client subclasses.')


def run_client(service_instance):
    try:
        service_instance.run()
    except KeyboardInterrupt:
        logger = logging.getLogger(service_instance.name)
        logger.info('exiting')
    finally:
        pass
        #with open(service_instance.log_file, 'a+') as f:
        #    f.write('Shutting down')
        #service_instance.send_status_update(CLIENT_SERVICE_STATUS_OFFLINE)
