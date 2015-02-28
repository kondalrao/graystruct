# -*- coding: utf-8 -*-
# Copyright (c) 2015 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import

import unittest

from ..encoder import _get_gelf_compatible_key


class TestBasic(unittest.TestCase):

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
