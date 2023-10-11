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

import os
import os.path

# Access SQL scripts withing the package
from pkg_resources import resource_filename
from importlib.resources import files

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# Database resources
SQL_SCHEMA           = files('zpida.db.sql').joinpath('schema.sql')
# The way to access there directories is deprecated ...
SQL_INITIAL_DATA_DIR = resource_filename(__name__, os.path.join('sql', 'initial' ))
SQL_UPDATES_DATA_DIR = resource_filename(__name__, os.path.join('sql', 'updates' ))
