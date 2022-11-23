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


class FileIterator:
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
		self.positionals = path_list
		self.root_dir = top

		self.current_state = self.STATES.UNRESOLVED_POSITIONAL  # signal this is the initial state of iterator

		self.counter = 0
		self.current_file = None

		self.current_oswalker = None
		self.current_oswalker_root = None
		self.current_oswalker_dirs = None
		self.current_oswalker_files = []  # set to empty list, so it's still poppable.

	def __next__(self):

		current_path = None
		logging.info(f"[i:{self.counter}] File iterator will look for the next file.")

		match self.current_state:
			case self.STATES.UNRESOLVED_POSITIONAL:
				logging.info(f"[i:{self.counter}] File iterator attempt to pop off an unresolved positional.")

				while current_path is None:
					# Attempt to pop next positional
					try:
						positional = Path(self.positionals.pop(0))
					except IndexError:
						self.current_state = self.STATES.END_ITER
						logging.info(f"[i:{self.counter}] File iterator is collapsing. All positionals have been exhausted.")
						raise StopIteration

					# Attempt to resolve next positional
					current_path = self.__resolve_positional(positional)

			case self.STATES.ON_OSWALK:
				logging.info(f"[i:{self.counter}] File iterator will attempt to extract another file from OSWalker obj.")
				current_path = self.__resume_walk()
				# TODO: What if this walk yields no files? They'll need to be a while-loop in here to keep walking, or pop positionals, for the next one.
				while current_path is None:
					# Attempt to pop next positional
					try:
						positional = Path(self.positionals.pop(0))
					except IndexError:
						self.current_state = self.STATES.END_ITER
						logging.info(f"[i:{self.counter}] File iterator is collapsing. All positionals have been exhausted.")
						raise StopIteration

					# Attempt to resolve next positional
					current_path = self.__resolve_positional(positional)

			case self.STATES.END_ITER:
				logging.info(f"[i:{self.counter}] Cannot return another file. All possible file paths have been exhausted.")
				raise StopIteration

			case _:
				logging.error(f"[i:{self.counter}] Iterator state '{self.current_state}' not recognized. How did you get here?")
				raise StopIteration

		self.counter += 1
		return current_path

	def __resolve_positional(self, positional):
		if not positional.exists():
			return None
		elif positional.exists():
			if positional.is_file():
				return positional

			elif positional.is_dir():
				self.current_state = self.STATES.ON_OSWALK
				self.current_oswalker = os.walk(os.path.join(self.root_dir, positional.name),
												topdown=self.OSWALKER_TOPDOWN,
												onerror=self.OSWALKER_FUNC_ON_ERROR,
												followlinks=self.OSWALKER_FOLLOWLINKS)

				# Walk until next file, or None if no file was found
				return self.__resume_walk()

	def __resolve_relative_path(self, filename):
		return Path(self.current_oswalker_root).relative_to(self.root_dir).joinpath(filename)

	def __resume_walk(self):

		current_file = None
		try:
			logging.info(f"[i:{self.counter}] Attempting to pop a remaining OSWalker files.")
			# current_file = Path(self.current_oswalker_root, self.current_oswalker_files.pop(0))
			current_file = self.__resolve_relative_path(self.current_oswalker_files.pop(0))

		except IndexError:
			while current_file is None:
				try:  # Try to take a step with the OSWalker
					logging.info(f"[i:{self.counter}] OSWalker taking next step.")
					(self.current_oswalker_root,
					 self.current_oswalker_dirs,
					 self.current_oswalker_files) = self.current_oswalker.__next__()

				except StopIteration:
					self.current_state = self.STATES.UNRESOLVED_POSITIONAL
					logging.info(f"[i:{self.counter}] OSWalker is collapsing. Setting state: {self.STATES.UNRESOLVED_POSITIONAL}")
					break

				# Try to pop a file from this walk frame
				try:
					logging.info(f"[i:{self.counter}] Attempting to pop a file in this walk frame.")
					current_file = self.__resolve_relative_path(self.current_oswalker_files.pop(0))
					# break

				except IndexError:
					logging.info(f"[i:{self.counter}] No more OSWalker files available in this walk frame!")
					pass

		logging.info(f"[i:{self.counter}] This walk is returning: {current_file}")
		return current_file

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
	parser.add_argument("positionals", type=str, nargs='+', help="A number of positional paths.")
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
	# for p in params.positionals:
	# 	path_obj = Path(p)
	# 	logging.debug("DBG: path_obj.name\t\t= {}".format(path_obj.name))
	# 	logging.debug("DBG: path_obj.resolve() = {}".format(path_obj.resolve()))
	# 	logging.debug("DBG: path_obj.is_dir()\t= {}".format(path_obj.is_dir()))
	# 	logging.debug("DBG: path_obj.is_file()\t= {}".format(path_obj.is_file()))

	# TEST - demonstrate file iterator can populate a list with all scoped files
	fpi = FileIterator(params.positionals)
	filepaths = [filepath for filepath in fpi]
	logging.info(f"**FINAL**: Discovered/Resolved file paths: {filepaths}")

	return 0


if __name__ == '__main__':
	params = parse_args(sys.argv[1:])
	sys.exit(main(params) if params else RC.SYNTAX_ERR.value)
