# -*- coding: utf-8 -*-
# Copyright (c) 2015 Simon Jagoe and Enthought Ltd
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import

import os
import json
import logging
import unittest

from mock import patch

from ..encoder import _get_gelf_compatible_key, GELFEncoder


class TestBasic(unittest.TestCase):
    maxDiff = None

    def test_get_gelf_compatible_key(self):
        # Given
        key = 'version'

        # When
        gelf_key = _get_gelf_compatible_key(key)

        # Then
        self.assertEqual(gelf_key, key)

        # Given
        key = 'nonstandard'

        # When
        gelf_key = _get_gelf_compatible_key(key)

        # Then
        self.assertEqual(gelf_key, '_' + key)

    def test_gelf_json_encoder_no_fqdn_explicit_host(self):
        # Given
        logger = logging.getLogger(__name__)
        log_method_name = 'warning'
        host = 'my_host'
        event = 'answered a question'
        line = 55
        function = 'some_function'
        user = 'simon'
        answer = 42
        swallow = 'european'

        encoder = GELFEncoder(fqdn=False, localname=host)
        event_dict = {
            'line': line,
            'file': __file__,
            'function': function,
            'user': user,
            'answer': answer,
            'swallow': swallow,
            'event': event,
        }
        initial_event_dict = event_dict.copy()

        expected = {
            'version': '1.1',
            'host': host,
            'short_message': event,
            'level': 4,  # syslog warning
            '_line': line,
            '_file': __file__,
            '_function': function,
            '_user': user,
            '_answer': answer,
            '_swallow': swallow,
            '_pid': os.getpid(),
            '_level_name': log_method_name.upper(),
            '_logger': logger.name,
        }

        # When
        event_json = encoder(logger, log_method_name, initial_event_dict)

        # Then
        # Event_dict is not mutated
        self.assertEqual(initial_event_dict, event_dict)
        new_event_dict = json.loads(event_json)
        self.assertEqual(new_event_dict, expected)

    @patch('socket.getfqdn')
    def test_gelf_json_encoder_fqdn(self, getfqdn):
        # Given
        host = 'my_host'
        getfqdn.return_value = host

        logger = logging.getLogger(__name__)
        log_method_name = 'warning'
        event = 'event'

        encoder = GELFEncoder()
        event_dict = {
            'event': event,
        }
        initial_event_dict = event_dict.copy()

        expected = {
            'version': '1.1',
            'host': host,
            'short_message': event,
            'level': 4,  # syslog warning
            '_pid': os.getpid(),
            '_level_name': log_method_name.upper(),
            '_logger': logger.name,
        }

        # When
        event_json = encoder(logger, log_method_name, initial_event_dict)

        # Then
        # Event_dict is not mutated
        self.assertEqual(initial_event_dict, event_dict)
        new_event_dict = json.loads(event_json)
        self.assertEqual(new_event_dict, expected)

    @patch('socket.gethostname')
    def test_gelf_json_encoder_hostname(self, gethostname):
        # Given
        host = 'my_host'
        gethostname.return_value = host

        logger = logging.getLogger(__name__)
        log_method_name = 'warning'
        event = 'event'

        encoder = GELFEncoder(fqdn=False)
        event_dict = {
            'event': event,
        }
        initial_event_dict = event_dict.copy()

        expected = {
            'version': '1.1',
            'host': host,
            'short_message': event,
            'level': 4,  # syslog warning
            '_pid': os.getpid(),
            '_level_name': log_method_name.upper(),
            '_logger': logger.name,
        }

        # When
        event_json = encoder(logger, log_method_name, initial_event_dict)

        # Then
        # Event_dict is not mutated
        self.assertEqual(initial_event_dict, event_dict)
        new_event_dict = json.loads(event_json)
        self.assertEqual(new_event_dict, expected)

    def test_gelf_json_encoder_with_exc_info(self):
        # Given
        logger = logging.getLogger(__name__)
        log_method_name = 'warning'
        host = 'my_host'
        event = 'answered a question'
        exception = 'Traceback\nValueError'

        encoder = GELFEncoder(fqdn=False, localname=host)
        event_dict = {
            'event': event,
            'exception': exception,
        }
        initial_event_dict = event_dict.copy()

        expected = {
            'version': '1.1',
            'host': host,
            'short_message': event,
            'full_message': event + '\n' + exception,
            'level': 4,  # syslog warning
            '_pid': os.getpid(),
            '_level_name': log_method_name.upper(),
            '_logger': logger.name,
        }

        # When
        event_json = encoder(logger, log_method_name, initial_event_dict)

        # Then
        # Event_dict is not mutated
        self.assertEqual(initial_event_dict, event_dict)
        new_event_dict = json.loads(event_json)
        self.assertEqual(new_event_dict, expected)
