import json
import logging
import os
import socket
import zlib

from graypy.handler import SYSLOG_LEVELS, GELFHandler as BaseGELFHandler
from graypy.rabbitmq import GELFRabbitHandler as BaseGELFRabbitHandler
from structlog._frames import _find_first_app_frame_and_name
from structlog.stdlib import _NAME_TO_LEVEL


STANDARD_GELF_KEYS = (
    'version',
    'host',
    'short_message',
    'full_message',
    'timestamp',
    'level',
    'line',
    'file',
)


def _get_gelf_compatible_key(key):
    if key in STANDARD_GELF_KEYS or key.startswith('_'):
        return key
    return '_{}'.format(key)


def add_app_context(logger, method_name, event_dict):
    f, name = _find_first_app_frame_and_name(['logging', __name__])
    event_dict['file'] = f.f_code.co_filename
    event_dict['line'] = f.f_lineno
    event_dict['function'] = f.f_code.co_name
    return event_dict


class GelfJsonEncoder(object):
    def __init__(self, fqdn=True, localname=None,
                 gelf_keys=STANDARD_GELF_KEYS):
        if fqdn:
            host = socket.getfqdn()
        elif localname is not None:
            host = localname
        else:
            host = socket.gethostname()
        self.host = host
        self.gelf_keys = frozenset(gelf_keys)

    def _translate_non_gelf_keys(self, event_dict):
        return {
            _get_gelf_compatible_key(key): value
            for key, value in event_dict.items()
        }

    def __call__(self, logger, method_name, event_dict):
        levelno = _NAME_TO_LEVEL[method_name]

        gelf_dict = {
            'version': '1.1',
            'host': self.host,
            'level': SYSLOG_LEVELS.get(levelno, levelno),
        }
        if 'message' in event_dict:
            message = event_dict['short_message'] = event_dict.pop('message')
        else:
            message = ''
        if 'exception' in event_dict:
            exc = event_dict.pop('exception')
            event_dict['full_message'] = '\n'.join([message, exc])

        gelf_dict['_pid'] = os.getpid()
        gelf_dict['_logger'] = logger.name
        gelf_dict['_level_name'] = logging.getLevelName(levelno)

        gelf_dict.update(self._translate_non_gelf_keys(event_dict))

        return json.dumps(gelf_dict)


class _CompressHandler(object):
    def makePickle(self, record):
        return zlib.compress(record.msg.encode('urf-8'))


class GELFHandler(_CompressHandler, BaseGELFHandler):
    pass


class GELFRabbitHandler(_CompressHandler, BaseGELFRabbitHandler):
    pass
