from __future__ import absolute_import

import os

from functools import partial

from celery.five import items
from kombu import Exchange, Queue
from kombu.utils import symbol_by_name

CSTRESS_QUEUE = os.environ.get('CSTRESS_QUEUE_NAME', 'c.stress')

templates = {}


def template(name=None):

    def _register(cls):
        templates[name or cls.__name__] = '.'.join([__name__, cls.__name__])
        return cls
    return _register


def use_template(app, template='default'):
    template = template.split(',')
    app.after_configure = partial(mixin_templates, template[1:])
    app.config_from_object(templates[template[0]])


def mixin_templates(templates, conf):
    return [mixin_template(template, conf) for template in templates]


def mixin_template(template, conf):
    cls = symbol_by_name(templates[template])
    conf.update(dict(
        (k, v) for k, v in items(vars(cls))
        if k.isupper() and not k.startswith('_')
    ))


def template_names():
    return ', '.join(templates)


@template()
class default(object):
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_DEFAULT_QUEUE = CSTRESS_QUEUE
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_QUEUES = [
        Queue(CSTRESS_QUEUE,
              exchange=Exchange(CSTRESS_QUEUE),
              routing_key=CSTRESS_QUEUE),
    ]
    BROKER_URL = os.environ.get('CSTRESS_BROKER', 'amqp://')
    CELERY_RESULT_BACKEND = os.environ.get('CSTRESS_BACKEND', 'rpc://')
    CELERYD_PREFETCH_MULTIPLIER = int(os.environ.get('CSTRESS_PREFETCH', 1))


@template()
class redis(default):
    BROKER_URL = os.environ.get('CSTRESS_BROKER', 'redis://')
    CELERY_RESULT_BACKEND = os.environ.get('CSTRESS_bACKEND', 'redis://')
    BROKER_TRANSPORT_OPTIONS = {'fanout_prefix': True}


@template()
class redistore(default):
    CELERY_RESULT_BACKEND = 'redis://'


@template()
class acks_late(default):
    CELERY_ACKS_LATE = True


@template()
class pickle(default):
    CELERY_ACCEPT_CONTENT = ['pickle', 'json']
    CELERY_TASK_SERIALIZER = 'pickle'
    CELERY_RESULT_SERIALIZER = 'pickle'


@template()
class confirms(default):
    BROKER_TRANSPORT_OPTIONS = {'confirm_publish': True}
