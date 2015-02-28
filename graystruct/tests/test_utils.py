# -*- coding: utf-8 -*-
# Copyright (c) 2015 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import

import logging
import unittest

from ..utils import add_app_context


class TestAddAppContext(unittest.TestCase):

    def test_add_app_context(self):
        # Given
        logger = logging.getLogger(__name__)

        # When
        event_dict = add_app_context(logger, 'warning', {})

        # Then
        self.assertEqual(
            event_dict,
            {
                'file': __file__,
                'function': 'test_add_app_context',
                'line': 22,
            },
        )
