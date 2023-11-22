# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
#  -------------------

import sys
import datetime
import argparse
import os.path
import logging
import traceback
import importlib

# -------------
# Local imports
# -------------

from ._version import __version__

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger()
package = __name__.split(".")[0]

# ------------------------
# Module utility functions
# ------------------------


def configure_logging(options):
    if options.verbose:
        level = logging.DEBUG
    elif options.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO

    log.setLevel(level)
    # Log formatter
    # fmt = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    # create console handler and set level to debug
    if options.console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG)
        log.addHandler(ch)
    # Create a file handler suitable for logrotate usage
    if options.log_file:
        # fh = logging.handlers.WatchedFileHandler(options.log_file)
        fh = logging.handlers.TimedRotatingFileHandler(options.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)

    if options.modules:
        modules = options.modules.split(',')
        for module in modules:
            logging.getLogger(module).setLevel(logging.DEBUG)


def valid_file(path):
    """File validator for the command line interface"""
    if not os.path.isfile(path):
        raise IOError(f"Not valid or existing file: {path}")
    return path


def valid_dir(path):
    """Directory validator for the command line interface"""
    if not os.path.isdir(path):
        raise IOError(f"Not valid or existing directory: {path}")
    return path


def valid_bool(boolstr):
    """Boolean text validator for the command line interface"""
    result = None
    if boolstr == 'True':
        result = True
    elif boolstr == 'False':
        result = False
    return result


def valid_date(datestr):
    """Date & time validator for the command line interface"""
    date = None
    for fmt in ['%Y-%m', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
        try:
            date = datetime.datetime.strptime(datestr, fmt)
        except ValueError:
            pass
    return date

# =================== #
# THE ARGUMENT PARSER #
# =================== #


def create_parser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser = argparse.ArgumentParser(prog="zpida", description="OSPOSEN TOOL")

    # -------------------------------
    # Global options to every command
    # -------------------------------

    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='Verbose output.')
    group.add_argument('-q', '--quiet',   action='store_true', help='Quiet output.')
    parser.add_argument('-c', '--console', action='store_true', help='Log to console.')
    parser.add_argument('-l', '--log-file', type=str, default=None, help='Optional log file')
    parser.add_argument('-m', '--modules', type=str, default=None, action='store', help='comma separated list of modules to activate debug level upon')
    

    # --------------------------
    # Create first level parsers
    # --------------------------

    subparser = parser.add_subparsers(dest='command')

    parser_db = subparser.add_parser('data', help='Database commands')
    parser_ida = subparser.add_parser('ida', help='Database commands')
  
    # ---------------------------------------
    # Create second level parsers for 'dbase' 
    # ---------------------------------------

    subparser = parser_db.add_subparsers(dest='subcommand')
    dbupd = subparser.add_parser('update',  help="Database schema update")

    # ---------------------------------------
    # Create second level parsers for 'ida' 
    # ---------------------------------------

    subparser = parser_ida.add_subparsers(dest='subcommand')
    idana = subparser.add_parser('analyze',  help="ZP analysis")
    grp = idana.add_mutually_exclusive_group(required=True)
    grp.add_argument('-f', '--file', type=valid_file, default=None, help='Analyze single file')
    grp.add_argument('-d', '--dir', type=valid_dir, default=None,  help='Analyze a directory of IDA files')

    return parser

# ================ #
# MAIN ENTRY POINT #
# ================ #


def main():
    """
    Utility entry point
    """
    try:
        options = create_parser().parse_args(sys.argv[1:])
        configure_logging(options)
        #name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
        #name = __name__
        name = "zpida"
        log.info(f"============== {name} {__version__} ==============")
        package = f"{name}"
        command = f"{options.command}"
        subcommand = f"{options.subcommand}"
        try:
            log.debug("loading command from module %s in package %s", command, package)
            command = importlib.import_module(command, package=package)
        except ModuleNotFoundError:	 # when debugging module in git source tree ...
            command = f".{options.command}"
            log.debug("retrying loading command from module %s in package %s", command, package)
            command = importlib.import_module(command, package=package)
        getattr(command, subcommand)(options)
    except AttributeError:
            log.critical("[%s] No subcommand was given ", __name__)
            traceback.print_exc()
    except KeyboardInterrupt:
        log.critical("[%s] Interrupted by user ", __name__)
    except Exception as e:
        log.critical("[%s] Fatal error => %s", __name__, str(e))
        traceback.print_exc()
    finally:
        pass


if __name__ == '__main__':
    main()
