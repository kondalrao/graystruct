# -*- coding: utf-8 -*-
# Copyright (c) 2015 Simon Jagoe and Enthought Ltd
# Portions copyright (c) 2011, Sever Băneşiu
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import

import amqp
from logging import Filter
from logging.handlers import SocketHandler

try:
    from urllib.parse import urlparse, unquote
except ImportError:
    from urlparse import urlparse
    from urllib import unquote

from .handler import _CompressHandler


_ifnone = lambda v, x: x if v is None else v


class GELFRabbitHandler(_CompressHandler, SocketHandler):
    """RabbitMQ / Graylog Extended Log Format handler.

    This is copied from ``graypy.rabbitmq`` and modified to use py-amqp
    (AMQP 0.9.1).  Additionally removes GELF-related options, which are
    handled by the :class:`graystruct.encoder.GELFEncoder` class.

    NOTE: this handler ingores all messages logged by amqp.

    :param url: RabbitMQ URL (ex: amqp://guest:guest@localhost:5672/).
    :param exchange: RabbitMQ exchange. Default 'logging.gelf'.
        A queue binding must be defined on the server to prevent
        log messages from being dropped.
    :param exchange_type: RabbitMQ exchange type (default 'fanout').

    """

    def __init__(self, url, exchange='logging.gelf', exchange_type='fanout',
                 virtual_host='/'):
        self.url = url
        parsed = urlparse(url)
        if parsed.scheme != 'amqp':
            raise ValueError('invalid URL scheme (expected "amqp"): %s' % url)
        host = parsed.hostname or 'localhost'
        port = _ifnone(parsed.port, 5672)
        virtual_host = virtual_host if not unquote(parsed.path[1:]) \
            else unquote(parsed.path[1:])
        self.cn_args = {
            'host': '%s:%s' % (host, port),
            'userid': _ifnone(parsed.username, 'guest'),
            'password': _ifnone(parsed.password, 'guest'),
            'virtual_host': virtual_host,
            'insist': False,
        }
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.virtual_host = virtual_host
        SocketHandler.__init__(self, host, port)
        self.addFilter(ExcludeFilter('amqp'))

    def makeSocket(self, timeout=1):
        return RabbitSocket(
            self.cn_args, timeout, self.exchange, self.exchange_type)


class RabbitSocket(object):

    def __init__(self, cn_args, timeout, exchange, exchange_type):
        self.cn_args = cn_args
        self.timeout = timeout
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.connection = amqp.Connection(
            connection_timeout=timeout, **self.cn_args)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange,
            type=self.exchange_type,
            durable=True,
            auto_delete=False,
        )

    def sendall(self, data):
        msg = amqp.Message(data, delivery_mode=2)
        self.channel.basic_publish(
            msg, exchange=self.exchange)

    def close(self):
        try:
            self.connection.close()
        except Exception:
            pass


class ExcludeFilter(Filter):

    def __init__(self, name):
        """Initialize filter.

        Initialize with the name of the logger which, together with its
        children, will have its events excluded (filtered out).
        """
        if not name:
            raise ValueError('ExcludeFilter requires a non-empty name')
        self.name = name
        self.nlen = len(name)

    def filter(self, record):
        return not (record.name.startswith(self.name) and (
            len(record.name) == self.nlen or record.name[self.nlen] == "."))
