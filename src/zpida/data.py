# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import logging

# ---------------------
# Thrid-party libraries
# ---------------------

import decouple

# ------------------------
# Own modules and packages
# ------------------------

from .dbase.utils import create_or_open_database

log = logging.getLogger(__name__)


def update(options):
	database_url = decouple.config('DATABASE_URL')
	connection = create_or_open_database(database_url)
