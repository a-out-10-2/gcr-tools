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
	# Default supported extensions
	SUPPORTED_READ_EXTENSIONS = {'wav', 'flac'}
	SUPPORTED_WRITE_EXTENSIONS = {'wav', 'aiff', 'aifc'}

	# OS Walker options
	OSWALKER_TOPDOWN = True
	OSWALKER_FUNC_ON_ERROR = None  # set func for Errors
	OSWALKER_FOLLOWLINKS = True

	class STATES(Enum):
		UNRESOLVED_POSITIONAL = 0
		ON_OSWALK = 1
		END_ITER = 2  # final state after all discernible filepaths have been exhausted

	def __init__(self, path_list, top=os.getcwd()):
		self.path_list = path_list
		self.root_dir = top

		self.current_state = self.STATES.UNRESOLVED_POSITIONAL  # signal this is the initial state of iterator

		self.counter = 0
		self.current_file = None

		self.current_oswalker = None
		self.current_oswalker_root = None
		self.current_oswalker_dirs = None
		self.current_oswalker_files = None

	def __next__(self):

		current_path = None

		match self.current_state:
			case self.STATES.UNRESOLVED_POSITIONAL:
				logging.info(f"File iterator is initializing. Will now inspect next positional.")

				current_path = self.__pop_next_existing_positional_path()
				if current_path.is_file():
					# Do Nothing. Leave current path to be returned.
					pass

				elif current_path.is_dir():
					self.current_state = self.STATES.ON_OSWALK
					self.current_oswalker = os.walk(os.path.join(self.root_dir, current_path.name),
													topdown=self.OSWALKER_TOPDOWN,
													onerror=self.OSWALKER_FUNC_ON_ERROR,
													followlinks=self.OSWALKER_FOLLOWLINKS)

					# Look for next file in OSWalker path
					try:
						self.__walk_next_directory()
						current_path = self.__pop_next_oswalker_filepath()
					except StopIteration:
						logging.debug("OSWalker is collapsing.")
						self.current_state = self.STATES.UNRESOLVED_POSITIONAL
						raise StopIteration

			case self.STATES.ON_OSWALK:

				# Look for next file in OSWalker path
				try:
					current_path = self.__pop_next_oswalker_filepath()
				except StopIteration:
					logging.debug("OSWalker is collapsing.")
					self.current_state = self.STATES.UNRESOLVED_POSITIONAL
					raise StopIteration

			case self.STATES.END_ITER:
				logging.info(f"File iterator has returned all possible possible filepaths. ({self.STATES.END_ITER})")
				raise StopIteration

			case _:
				logging.error(f"Iterator state '{self.current_state}' not recognized. How did you get here?")
				raise StopIteration

		return current_path

	def __pop_next_existing_positional_path(self):
		"""
		:raises IndexError: And expect it to happen for end signal.
		:return: new_path
		"""
		new_path = Path(self.path_list.pop(0))
		while not new_path.exists():
			logging.debug(f"new_path: '{new_path}', does not exist, popping next positional path")
			new_path = Path(self.path_list.pop(0))

		return new_path

	def __pop_next_oswalker_filepath2(self):
		new_path = None
		return new_path

	def __pop_next_oswalker_filepath(self):

		new_path = None

		try:
			new_path = Path(self.current_oswalker_files.pop(0))

		except IndexError:
			try:
				found_file = False
				self.__walk_next_directory()

				while found_file is False:
					if len(self.current_oswalker_files) > 0:
						new_path = Path(self.current_oswalker_files.pop(0))
						found_file = True
					else:
						self.__walk_next_directory()

			except StopIteration:
				raise StopIteration

		return new_path

	def __walk_next_directory(self):
		self.current_oswalker_root, \
		self.current_oswalker_dirs, \
		self.current_oswalker_files = \
			self.current_oswalker.__next__()

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
											 message="(status: {}, "
													 "message: '{}'".format(status,
																			message))
		def error(self, message):
			raise argparse.ArgumentError(argument=None, message=message)

	# Constructing argument parser
	parser = _ArgumentParser(description="* GCR Slicer |/-\\")
	parser.add_argument("path_list", type=str, nargs='+', help="A number of positional paths.")
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
	# logging.debug(f"webrtcvad: {dir(webrtcvad)}")

	# Read input positionals and resolve them to a list/iterator of filepaths.
	# for p in params.path_list:
	# 	path_obj = Path(p)
	# 	logging.debug("DBG: path_obj.name\t\t= {}".format(path_obj.name))
	# 	logging.debug("DBG: path_obj.resolve() = {}".format(path_obj.resolve()))
	# 	logging.debug("DBG: path_obj.is_dir()\t= {}".format(path_obj.is_dir()))
	# 	logging.debug("DBG: path_obj.is_file()\t= {}".format(path_obj.is_file()))

	# TEST - demonstrate file iterator can populate a list with all scoped files
	fpi = FilePathsIterator(params.path_list)
	filepaths = [filepath for filepath in fpi]
	logging.info(f"**FINAL**: Discovered/Resolved file paths: {filepaths}")

	return 0


if __name__ == '__main__':
	params = parse_args(sys.argv[1:])
	sys.exit(main(params) if params else RC.SYNTAX_ERR.value)
