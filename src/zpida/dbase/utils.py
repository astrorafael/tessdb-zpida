# ----------------------------------------------------------------------
# Copyright (c) 2022
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import os.path
import glob
import uuid
import logging
import sqlite3

from importlib.resources import files

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# Database resources
SQL_SCHEMA           = files('zpida.dbase.sql').joinpath('schema.sql')
SQL_INITIAL_DATA_DIR = files('zpida.dbase.sql.initial')
try:
    SQL_UPDATES_DATA_DIR = files('zpida.dbase.sql.updates')
except ModuleNotFoundError:
    SQL_UPDATES_DATA_DIR = None # Whne there are no updates

# -------------------
# Third party imports
# -------------------

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

VERSION_QUERY = "SELECT value from config_t WHERE section ='database' AND property = 'version'"

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# ------------------------
# Module Utility Functions
# ------------------------

def _filter_factory(connection):
    cursor = connection.cursor()
    cursor.execute(VERSION_QUERY)
    result = cursor.fetchone()
    if not result:
        raise NotImplementedError(VERSION_QUERY)
    version = int(result[0])
    return lambda path: int(os.path.basename(path)[:2]) > version


# -------------------------
# Module private functions
# -------------------------

def _create_database(dbase_path):
    '''Creates a Database file if not exists and returns a connection'''
    new_database = False
    output_dir = os.path.dirname(dbase_path)
    if not output_dir:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(dbase_path):
        with open(dbase_path, 'w') as f:
            pass
        new_database = True
    return sqlite3.connect(dbase_path), new_database


def _create_schema(connection, schema_resource, initial_data_dir_path, updates_data_dir, query=VERSION_QUERY):
    created = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Exception:
        created = False
    if not created:
        connection.executescript(schema_resource.read_text())
        log.debug("Created data model from %s", os.path.basename(schema_resource))
        file_list = [sql_file for sql_file in initial_data_dir_path.iterdir()]
        for sql_file in file_list:
            log.debug("Populating data model from %s", os.path.basename(sql_file))
            connection.executescript(sql_file.read_text())
    elif updates_data_dir is not None:
        filter_func = _filter_factory(connection)
        file_list = sorted([sql_file for sql_file in updates_data_dir.iterdir()])
        file_list = list(filter(filter_func, file_list))
        for sql_file in file_list:
            print("Applying updates to data model from %s",os.path.basename(sql_file))
            connection.executescript(sql_file.read_text())
    else:
        file_list = list()
    connection.commit()
    return not created, file_list

# -------------------------
# UUID and version handling
# -------------------------

def _read_database_version(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "version";'
    cursor.execute(query)
    version = cursor.fetchone()[0]
    return version

def _write_database_uuid(connection):
    guid = str(uuid.uuid4())
    cursor = connection.cursor()
    param = {'section': 'database','property':'uuid','value': guid}
    cursor.execute(
        '''
        INSERT INTO config_t(section,property,value) 
        VALUES(:section,:property,:value)
        ''',
        param
    )
    connection.commit()
    return guid

def _make_database_uuid(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "uuid";'
    cursor.execute(query)
    guid = cursor.fetchone()
    if guid:
        try:
            uuid.UUID(guid[0])  # Validate UUID
        except ValueError:
            guid = _write_database_uuid(connection)
        else:
            guid = guid[0]
    else:
        guid = _write_database_uuid(connection)
    return guid

# ----------------
# Exported funtion
# ----------------

def create_or_open_database(url):
    connection, new_database = _create_database(url)
    if new_database:
            log.warn("Created new database file: %s", url)
    just_created, file_list = _create_schema(connection, SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR)
    if just_created:
        for sql_file in file_list:
            log.warn("Populated data model from %s", os.path.basename(sql_file))
    else:
        for sql_file in file_list:
            log.warn("Applied updates to data model from %s", os.path.basename(sql_file))
    version = _read_database_version(connection)
    guid    = _make_database_uuid(connection)
    log.info("Open database: %s, version = %s, UUID = %s", url, version, guid)
    connection.commit()
    return connection

__all__ = [
    "create_or_open_database",
]
