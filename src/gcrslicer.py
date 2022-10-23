#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#   Copyright © <2022> Andrew Moe
# -----------------------------------------------------------------------------
import argparse
import logging
import os
from pathlib import Path
import sys

import webrtcvad

__version__ = 0.0

# Exportable API
__all__ = ['main', 'parse_args']


class FilePathsIterator:
	FOLLOWLINKS = True
	SUPPORTED_READ_EXTENSIONS = {'wav', 'flac'}
	SUPPORTED_WRITE_EXTENSIONS = {'wav', 'aiff', 'aifc'}

	def __init__(self, audio_file_or_dir_paths):
		self.in_paths = audio_file_or_dir_paths

	def __next__(self):
		path_obj = Path(self.in_paths.pop(0))
		return path_obj

	def __iter__(self):
		return self


class GCRArgumentParser(argparse.ArgumentParser):
	""" An extension of ArgumentParser that throws an ArgumentError on syntax error. Instead of sys.exit().
	"""
	FLAG_HELP = "--help"

	def __init__(self, description):
		super().__init__(description=description, exit_on_error=False)

	def exit(self, status=0, message=None):
		if status:
			raise argparse.ArgumentError(argument=None, message="(status: {}, message: '{}'".format(status, message))

	def error(self, message):
		raise argparse.ArgumentError(argument=None, message=message)


def parse_args(*args, **kwargs):
	"""Parse the arguments received from STDIN.
	param args: The string arguments to be parsed.
	return params: The arguments parsed into parameters.
	rtype: argparse.Namespace
	"""
	# Constructing argument parser
	parser = GCRArgumentParser(description="* GCR Slicer |/-\\")
	parser.add_argument("audio_file_or_dir_paths", type=str, nargs='+', help="A number of positional paths.")
	mutux = parser.add_mutually_exclusive_group()
	mutux.required = True  # Require a mutux option
	mutux.add_argument("--analyze", default=False, action='store_true', help="Analyze and plot silence of each file.")
	mutux.add_argument("--write-dir", type=str, default=None, help="Path to write audio file slices.")
	parser.add_argument("-v", "--verbose", action="count", default=0, help="Amount of output during runtime.")
	parser.add_argument("--version", action='version', version='cli %s' % __version__)

	# Process and return parameters
	try:
		params = parser.parse_args(*args, **kwargs)
	except argparse.ArgumentError as ae:
		if parser.FLAG_HELP not in list(*args):
			print(f"ArgumentError: {ae} (args: {list(*args)})", file=sys.stderr)
		params = None

	return params


def main(params):
	"""
	Execute the main method of the program.
	param params: The parameters that will dictate the functionality of the program.
	:return: The final return code of the program.
	:rtype: int
	"""

	# Set up logging
	if params.verbose == 1:
		logging.basicConfig(format='%(message)s', level=logging.INFO)
	elif params.verbose == 2:
		logging.basicConfig(format='%(message)s', level=logging.DEBUG)

	# DBG
	logging.debug("params: {}".format(params))
	logging.info("webrtcvad: {}".format(dir(webrtcvad)))

	exec_cwd = os.getcwd()

	# Read input positionals and resolve them to a list/iterator of filepaths.
	# for p in params.audio_file_or_dir_paths:
	# 	path_obj = Path(p)
	# 	logging.debug("DBG: path_obj.name\t\t= {}".format(path_obj.name))
	# 	logging.debug("DBG: path_obj.resolve() = {}".format(path_obj.resolve()))
	# 	logging.debug("DBG: path_obj.is_dir()\t= {}".format(path_obj.is_dir()))
	# 	logging.debug("DBG: path_obj.is_file()\t= {}".format(path_obj.is_file()))
	fpi = FilePathsIterator(params.audio_file_or_dir_paths)

	return 0


if __name__ == '__main__':
	args = sys.argv[1:]
	params = parse_args(args)
	if params is None:
		rc = 1
	else:
		rc = main(params)
	sys.exit(rc)
