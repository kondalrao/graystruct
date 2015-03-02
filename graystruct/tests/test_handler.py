# -*- coding: utf-8 -*-
# Copyright (c) 2015 Simon Jagoe and Enthought Ltd
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import

import json
import logging
import os
import unittest
import zlib

from structlog import wrap_logger

from mock import Mock

from ..encoder import GELFEncoder
from ..handler import GELFHandler
from ..rabbitmq import GELFRabbitHandler


class TestingGELFHandler(GELFHandler):

    def __init__(self, mock, *args, **kwargs):
        super(TestingGELFHandler, self).__init__(*args, **kwargs)
        self._mock = mock

    def send(self, s):
        self._mock(s)


class TestingGELFRabbitHandler(GELFRabbitHandler):

    def __init__(self, mock, *args, **kwargs):
        super(TestingGELFRabbitHandler, self).__init__(*args, **kwargs)
        self._mock = mock

    def makeSocket(self, timeout=1):
        return self._mock


class TestGELFHandler(unittest.TestCase):

    def setUp(self):
        self.std_logger = std_logger = logging.Logger(__name__, logging.DEBUG)
        self.logger = wrap_logger(
            std_logger, processors=[GELFEncoder(fqdn=False, localname='host')])
        self.expected = {
            'version': '1.1',
            'host': 'host',
            'level': 4,  # syslog WARNING
            'short_message': 'event',
            '_pid': os.getpid(),
            '_level_name': 'WARNING',
            '_logger': std_logger.name,
        }

    def test_direct_handler(self):
        # Given
        std_logger = self.std_logger
        collector = Mock()
        handler = TestingGELFHandler(collector, 'localhost')
        std_logger.addHandler(handler)

        # When
        self.logger.warning('event')

        # Then
        self.assertEqual(collector.call_count, 1)
        args, kwargs = collector.call_args

        self.assertEqual(len(args), 1)
        self.assertEqual(len(kwargs), 0)

        event_json = zlib.decompress(args[0])
        event_dict = json.loads(event_json.decode('utf-8'))
        self.assertEqual(event_dict, self.expected)

    def test_rabbit_handler(self):
        # Given
        std_logger = self.std_logger
        socket = Mock()
        collector = Mock()
        socket.sendall = collector
        handler = TestingGELFRabbitHandler(socket, 'amqp://localhost')
        std_logger.addHandler(handler)

        # When
        self.logger.warning('event')

        # Then
        self.assertEqual(collector.call_count, 1)
        args, kwargs = collector.call_args

        self.assertEqual(len(args), 1)
        self.assertEqual(len(kwargs), 0)

        event_json = zlib.decompress(args[0])
        event_dict = json.loads(event_json.decode('utf-8'))
        self.assertEqual(event_dict, self.expected)
