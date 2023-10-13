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
import re
import glob
import math
import sqlite3
import logging
import statistics

# ---------------------
# Thrid-party libraries
# ---------------------

import decouple

# ------------------------
# Own modules and packages
# ------------------------

from .dbase.utils import create_or_open_database

# ----------------
# Global variables
# ----------------

log = logging.getLogger(__name__)

mac_re = re.compile(r"([0-9a-fA-F]{1,2}:[0-9a-fA-F]{1,2}:[0-9a-fA-F]{1,2}:[0-9a-fA-F]{1,2}:[0-9a-fA-F]{1,2}:[0-9a-fA-F]{1,2})")
name_re = re.compile(r"# Instrument ID: (\w+)")
tzone_re = re.compile(r"# Local timezone: (\S+)")

# ----------
# SQL Access
# ----------

def insert_ida_rows(connection, rows):
	cursor = connection.cursor()
	sql = '''
		INSERT OR REPLACE INTO ida_summary_t VALUES
		(
			:filename,
			:name,
			:mac,
			:timezone,
			:t0,
			:t1,
			:data_rows,
			:valid_rows,
			:computed_zp_median,
			:computed_zp_stdev,
			:computed_zp_min,
			:computed_zp_max,
			:tessdb_zp_median,
			:tessdb_zp_stdev
		)
		'''
	cursor.executemany(sql, rows)
	connection.commit()

# ------------------
# Auxiliar functions
# ------------------

def scan_non_empty_dirs(root_dir, depth=None):
    if os.path.basename(root_dir) == '':
        root_dir = root_dir[:-1]
    dirs = set(dirpath for dirpath, dirs, files in os.walk(root_dir) if files)
    dirs.add(root_dir)   # Add it for images just under the root_dir folder
    if depth is None:
        return sorted(list(dirs))
    L = len(root_dir.split(sep=os.sep))
    return sorted(list(filter(lambda d: len(d.split(sep=os.sep)) - L <= depth, dirs)))

def analyze_directory(directory):
	summaries = list()
	file_list  = sorted(glob.glob(os.path.join(directory, '*.dat')))
	for path in file_list:
		summary = analyze_single_file(path)
		if summary is not None:
			summaries.append(summary)
	log.info("Handling %d IDA files in %s",len(summaries), os.path.basename(directory))
	return summaries

def analyze_single_file(path):
	with open(path) as f:
		log.debug("processing %s", path)
		header = [ f.readline().strip() for i in range(35) ]
		name = re.search(name_re, header[5]).group(1)
		try:
			mac = re.search(mac_re, header[18]).group(1)
		except AttributeError:
			log.error("%s: MAC Format error => %s",path,header[18])
			mac = None
		try:
			timezone = re.search(tzone_re, header[9]).group(1)
		except AttributeError:
			log.error("%s: Timezone Format error => %s",path,header[9])
			timezone = None
		tessdb_zp_list = list()
		computed_zp_list = list()
		timestamp_list = list()
		for i, line in enumerate(f,1):
			items = line.split(';')
			try:
				timestamp = items[0]
				tessdb_zp = float(items[-1])
				mag = float(items[-2])
				freq = float(items[-3]) 
				computed_zp = mag + 2.5 * math.log10(freq)
			except:
				continue
			else:
				tessdb_zp_list.append(tessdb_zp)
				computed_zp_list.append(computed_zp)
				timestamp_list.append(timestamp)
	if computed_zp_list:
		result = dict()
		result['computed_zp_median'] = round(statistics.median(computed_zp_list),2)
		try:
			result['computed_zp_stdev'] = round(statistics.stdev(computed_zp_list, result['computed_zp_median']),3)
		except statistics.StatisticsError:
			result['computed_zp_stdev'] = math.inf
		result['computed_zp_max'] = round(max(computed_zp_list),2)
		result['computed_zp_min'] = round(min(computed_zp_list),2)
		result['tessdb_zp_median'] = statistics.median(tessdb_zp_list)
		try:
			result['tessdb_zp_stdev'] = round(statistics.stdev(tessdb_zp_list, result['tessdb_zp_median']),3)
		except statistics.StatisticsError:
			result['tessdb_zp_stdev'] =  math.inf
		result['valid_rows'] = len(computed_zp_list)
		result['data_rows'] = i
		result['t0'] = min(timestamp_list)
		result['t1'] = max(timestamp_list)
		result['mac'] = mac
		result['name'] = name
		result['timezone'] = timezone
		result['filename'] = os.path.basename(path)
		#log.debug("%s", result)
	else:
		log.warn("Empty IDA file %s", path)
		result = None
	return result


def analyze(options):
	database_url = decouple.config('DATABASE_URL')
	connection = create_or_open_database(database_url)
	if options.file:
		summary = analyze_single_file(options.file)
		if summary is not None:
			insert_ida_rows(connection, [summary])
	elif options.dir:
		folders = scan_non_empty_dirs(options.dir)
		for folder in folders:
			summaries = analyze_directory(folder)
			if summaries:
				insert_ida_rows(connection, summaries)

