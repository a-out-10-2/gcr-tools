#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#   Copyright © <2022> Andrew Moe
# -----------------------------------------------------------------------------
import argparse
from enum import Enum
import logging
import os
from pathlib import Path
import sys

import webrtcvad

__version__ = 0.0

# Exportable API
# __all__ = ['main', 'parse_args']


class FilePathsIterator:
	SUPPORTED_READ_EXTENSIONS = {'wav', 'flac'}
	SUPPORTED_WRITE_EXTENSIONS = {'wav', 'aiff', 'aifc'}

	OSWALKER_TOPDOWN = True
	OSWALKER_FUNC_ON_ERROR = None  # set func for Errors
	OSWALKER_FOLLOWLINKS = True

	def __init__(self, audio_file_or_dir_paths, top=os.getcwd()):
		self.in_paths = audio_file_or_dir_paths
		self.top = top

		self.current_filepath = None
		self.current_walker = None

	def __next__(self):
		""":return: Return a new pathlib.Path object of next file
		:raises: StopIteration to signal iterator's emptiness.
		"""

		# Attempt to resolve the next positional path.
		current_positional = None
		try:
			# TODO: If resuming from previous os.walk, don't pop a pos
			current_positional = self.__pop_next_existing_positional_path()
		except StopIteration:
			logging.debug(f"caught StopIteration during __pop_next_positional_path(), raising StopIteration")
			raise StopIteration

		logging.debug(f"SUCCESS! positional '{current_positional}' has been popped!")
		logging.debug(f"new_path='{current_positional}'")
		logging.debug(f"\texists?='{current_positional.exists()}'")
		logging.debug(f"\tis_dir?='{current_positional.is_dir()}'")
		logging.debug(f"\tis_file?='{current_positional.is_file()}'")

		if current_positional.is_dir():
			current_dir_scope = os.path.join(self.top, current_positional.name)
			self.current_walker = os.walk(current_dir_scope, topdown=self.OSWALKER_TOPDOWN, onerror=self.OSWALKER_FUNC_ON_ERROR, followlinks=self.OSWALKER_FOLLOWLINKS)
			# TODO: Walk os.dir() until the first file is found, return it
			root, dirs, files = self.current_walker.__next__()
			logging.debug(f"OS_WALKER START (root='{root}', dirs={dirs}, files={files})")
			# OS_WALKER START (root='C:\Users\Gifty\PycharmProjects\gcr-tools\data', dirs=[], files=['21 Tom Cat, Individual Meows.flac', '34 Tom Cat, Meowing.flac', '35 Tom Cat, Purring.flac', '46 Tom Cat Growling.flac', '49 Tom Cat Hiss.flac'])
			# OS_WALKER START (root='C:\Users\Gifty\PycharmProjects\gcr-tools\data2', dirs=[], files=['somefile.blr'])
			pass

		#
		# if current_positional.is_file():
		# 	self.current_filepath = current_positional
		# 	# TODO: Cross-check file exentions agains list, skip if not on it

		return current_positional

	def __pop_next_existing_positional_path(self):
		"""
		:raises StopIteration:
		:return:
		"""
		try:
			new_path = Path(self.in_paths.pop(0))
			while not new_path.exists():
				logging.debug(f"new_path: '{new_path}', does not exist, popping next positional path")
				new_path = Path(self.in_paths.pop(0))
		except IndexError as ie:
			logging.debug(f"caught IndexError ie:'{ie}' when popping positional, raising StopIteration")
			raise StopIteration

		return new_path

	def __iter__(self):
		return self


class RC(Enum):
	PASS = 0
	SYNTAX_ERR = 1


def parse_args(*args, **kwargs):
	"""Parse the arguments received from STDIN.
	param args: The string arguments to be parsed.
	return params: The arguments parsed into parameters.
	rtype: argparse.Namespace
	"""

	class _ArgumentParser(argparse.ArgumentParser):
		""" Supress exit and raise exceptions on syntax errors
		"""
		FLAG_HELP = "--help"

		def __init__(self, description):
			super().__init__(description=description, exit_on_error=False)

		def exit(self, status=0, message=None):
			if status:
				raise argparse.ArgumentError(argument=None,
											 message="(status: {}, message: '{}'".format(status, message))

		def error(self, message):
			raise argparse.ArgumentError(argument=None, message=message)

	# Constructing argument parser
	parser = _ArgumentParser(description="* GCR Slicer |/-\\")
	parser.add_argument("audio_file_or_dir_paths", type=str, nargs='+', help="A number of positional paths.")
	mutux = parser.add_mutually_exclusive_group()
	mutux.required = True  # Require a mutux option
	mutux.add_argument("--analyze", default=False, action='store_true', help="Analyze and plot silence of each file.")
	mutux.add_argument("--write-dir", type=str, default=None, help="Path to write audio file slices.")
	parser.add_argument("-v", "--verbose", action="count", default=0, help="Amount of output during runtime.")
	parser.add_argument("--version", action='version', version='cli %s' % __version__)

	# Process and return parameters
	params = None
	try:
		params = parser.parse_args(*args, **kwargs)
	except argparse.ArgumentError as ae:
		if parser.FLAG_HELP not in list(*args):
			print(f"ArgumentError: {ae} (args: {list(*args)})", file=sys.stderr)

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
	logging.debug(f"params: {params}")
	logging.debug(f"webrtcvad: {dir(webrtcvad)}")

	# Read input positionals and resolve them to a list/iterator of filepaths.
	# for p in params.audio_file_or_dir_paths:
	# 	path_obj = Path(p)
	# 	logging.debug("DBG: path_obj.name\t\t= {}".format(path_obj.name))
	# 	logging.debug("DBG: path_obj.resolve() = {}".format(path_obj.resolve()))
	# 	logging.debug("DBG: path_obj.is_dir()\t= {}".format(path_obj.is_dir()))
	# 	logging.debug("DBG: path_obj.is_file()\t= {}".format(path_obj.is_file()))

	fpi = FilePathsIterator(params.audio_file_or_dir_paths)
	filepaths = [filepath for filepath in fpi]
	logging.info(f"**FINAL**: Discovered/Resolved file paths: {filepaths}")

	return 0


if __name__ == '__main__':
	params = parse_args(sys.argv[1:])
	sys.exit(main(params) if params else RC.SYNTAX_ERR.value)
