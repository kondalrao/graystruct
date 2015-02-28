# -*- coding: utf-8 -*-
# Copyright (c) 2015 Simon Jagoe
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


class TestingGELFHandler(GELFHandler):

    def __init__(self, mock, *args, **kwargs):
        super(TestingGELFHandler, self).__init__(*args, **kwargs)
        self._mock = mock

    def send(self, s):
        self._mock(s)


class TestGELFHandler(unittest.TestCase):

    def test(self):
        # Given
        std_logger = logging.getLogger(__name__)
        collector = Mock()
        handler = TestingGELFHandler(collector, 'localhost')
        std_logger.addHandler(handler)
        std_logger.setLevel(logging.DEBUG)
        logger = wrap_logger(
            std_logger, processors=[GELFEncoder(fqdn=False, localname='host')])

        expected = {
            'version': '1.1',
            'host': 'host',
            'level': 4,  # syslog WARNING
            'short_message': 'event',
            '_pid': os.getpid(),
            '_level_name': 'WARNING',
            '_logger': std_logger.name,
        }

        # When
        logger.warning('event')

        # Then
        self.assertEqual(collector.call_count, 1)
        args, kwargs = collector.call_args

        self.assertEqual(len(args), 1)
        self.assertEqual(len(kwargs), 0)

        event_json = zlib.decompress(args[0])
        event_dict = json.loads(event_json.decode('utf-8'))
        self.assertEqual(event_dict, expected)
