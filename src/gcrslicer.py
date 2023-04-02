#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#   Copyright © <2022> Andrew Moe
# -----------------------------------------------------------------------------
""" CLI utility for slicing audio files for SampleBrain."""
import argparse
import itertools
from itertools import filterfalse, takewhile
from enum import Enum
import logging
import os
from pathlib import Path
from typing import Generator
import sys

from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt

# import webrtcvad

# Default supported extensions
SUPPORTED_READ_EXTENSIONS = {'wav'}  # , 'flac'}
# SUPPORTED_WRITE_EXTENSIONS = {'wav', 'aiff', 'aifc'}

__version__ = 0.0

# Exportable API
# __all__ = ['main', 'parse_args']

def file_iterator2(path_list, top=os.getcwd(), file_ext_filter=None):
	positionals = [Path(p) for p in path_list]
	root_dir = top
	file_extension_filters = file_ext_filter if file_ext_filter else []
	current_oswalker = None

	for positional in takewhile(lambda p: p is not None, positionals):

		# Skip positional, if it doesn't exist
		if not positional.exists:
			continue

		# Yield, if a file
		if positional.is_file():
			matches_extension = True

			# Yield path, if it matches criteria
			for ext in file_extension_filters:
				matches_extension = False
				if positional.name.lower().endswith(ext):
					matches_extension = True
					break

			if matches_extension:
				yield positional
			else:
				continue

		# Bring out OSWalker if it's a file
		elif positional.is_dir():
			current_oswalker = os.walk(
				os.path.join(root_dir, positional.name),
				topdown=FileIterator.OSWALKER_TOPDOWN,
				onerror=FileIterator.OSWALKER_FUNC_ON_ERROR,
				followlinks=FileIterator.OSWALKER_FOLLOWLINKS
			)

			# Yield, all files found in OSWalker
			for osw_root, _, osw_files in current_oswalker:
				for osw_file in osw_files:

					# Yield path, if it matches criteria
					matches_extension = True
					osw_pathfile = Path(osw_root).relative_to(root_dir).joinpath(osw_file)
					for ext in file_extension_filters:
						matches_extension = False
						if osw_pathfile.name.lower().endswith(ext):
							matches_extension = True
							break

					if matches_extension:
						yield osw_pathfile
					else:
						continue

		else:
			# Unknown state
			print("DBG: entered unknown \"file\" state.")
			return

	print("DBG: End of file_iterator2")
	return


class FileIterator:
	"""An iterator that returns files from a provided list of search paths."""
	# OS Walker options
	OSWALKER_TOPDOWN = True
	OSWALKER_FUNC_ON_ERROR = None  # set func for Errors
	OSWALKER_FOLLOWLINKS = True

	class STATES(Enum):
		"""Operational states of the FileIterator"""
		UNRESOLVED_POSITIONAL = 0
		ON_OSWALK = 1
		END_ITER = 2  # final state after all discernible filepaths have been exhausted

	class OSWalkerState:
		"""A class that tracks the state of each walk frame."""
		current_oswalker: Generator
		current_oswalker_root: str
		current_oswalker_dirs: list
		current_oswalker_files: list

		def __init__(self, current_oswalker):
			self.current_oswalker = current_oswalker
			self.current_oswalker_root = None
			self.current_oswalker_dirs = None
			self.current_oswalker_files = []

		def walk(self):
			"""Step into the next OSWalker directory"""
			self.current_oswalker_root, \
			self.current_oswalker_dirs, \
			self.current_oswalker_files = self.current_oswalker.__next__()

	# class Parent(object):
	# 	def __new__(cls, value, *args, **kwargs):
	# 		print
	# 		'my value is', value
	# 		return object.__new__(cls, *args, **kwargs)

	# fpi_filtered = itertools.filterfalse(fpi.__fileext_filter_predicate__, fpi)
	# found_filelist = list(fpi_filtered)
	#
	# def __new__(cls, *args, filters=None, **kwargs):
	#
	# 	if not filters:
	# 		cls.filters = []
	#
	# 	def __fileext_filter_predicate__(filepath, inner_filters=cls.filters):
	# 		"""Filter filenames by extension. Predicate filter for itertools."""
	# 		skip_file = True
	# 		for sel_ext in inner_filters:
	# 			if filepath.name.lower().endswith(sel_ext):
	# 				skip_file = False
	# 				break
	# 		return skip_file
	#
	# 	return itertools.filterfalse(__fileext_filter_predicate__, cls(*args, **kwargs))

	def __init__(self, path_list, top=os.getcwd(), file_ext_filter=None):
		self.positionals = path_list
		self.root_dir = top
		self.file_extension_filters = file_ext_filter if file_ext_filter else []  # a list of file extension strings
		self.current_state = self.STATES.UNRESOLVED_POSITIONAL  # signal this is the initial state of iterator

		self.counter = 0
		self.current_file = None

		self.oswalker_state = None

	def __next__(self):
		current_path = None
		logging.debug(f"[i:{self.counter}] File iterator will look for the next file.")

		match self.current_state:
			case self.STATES.UNRESOLVED_POSITIONAL:
				logging.debug(f"[i:{self.counter}] File iterator attempt to pop off an unresolved positional.")

				while current_path is None:
					# Attempt to pop next positional
					try:
						positional = Path(self.positionals.pop(0))
					except IndexError as ie:
						self.current_state = self.STATES.END_ITER
						logging.debug(
							f"[i:{self.counter}] File iterator is collapsing. All positionals have been exhausted.")
						raise StopIteration from ie

					# Attempt to resolve next positional
					current_path = self.__resolve_positional(positional)

			case self.STATES.ON_OSWALK:
				logging.debug(
					f"[i:{self.counter}] File iterator will attempt to extract another file from OSWalker obj.")
				current_path = self.__resume_walk()
				while current_path is None:
					# Attempt to pop next positional
					try:
						positional = Path(self.positionals.pop(0))
					except IndexError as ie:
						self.current_state = self.STATES.END_ITER
						logging.debug(
							f"[i:{self.counter}] File iterator is collapsing. All positionals have been exhausted.")
						raise StopIteration from ie

					# Attempt to resolve next positional
					current_path = self.__resolve_positional(positional)

			case self.STATES.END_ITER:
				logging.debug(
					f"[i:{self.counter}] Cannot return another file. All possible file paths have been exhausted.")
				raise StopIteration

			case _:
				logging.error(
					f"[i:{self.counter}] Iterator state '{self.current_state}' not recognized. How did you get here?")
				raise StopIteration

		self.counter += 1
		return current_path

	def __resolve_positional(self, positional):
		resolved_positional = None
		if positional.exists():
			if positional.is_file():
				resolved_positional = positional

			elif positional.is_dir():
				self.current_state = self.STATES.ON_OSWALK
				self.oswalker_state = self.OSWalkerState(
					os.walk(
						os.path.join(self.root_dir, positional.name),
						topdown=self.OSWALKER_TOPDOWN,
						onerror=self.OSWALKER_FUNC_ON_ERROR,
						followlinks=self.OSWALKER_FOLLOWLINKS))

				# Walk until next file, or None if no file was found
				resolved_positional = self.__resume_walk()

			else:
				raise ValueError(f"Positional is neither a directory, nor a file. (positional={positional})")

		return resolved_positional

	def __resolve_to_relative_path(self, filename):
		return Path(self.oswalker_state.current_oswalker_root).relative_to(self.root_dir).joinpath(filename)

	def __resume_walk(self):
		current_file = None
		try:
			logging.debug(f"[i:{self.counter}] Attempting to pop a remaining OSWalker files.")
			current_file = self.__resolve_to_relative_path(self.oswalker_state.current_oswalker_files.pop(0))

		except IndexError:
			while current_file is None:
				try:  # Try to take a step with the OSWalker
					logging.debug(f"[i:{self.counter}] OSWalker taking next step.")
					self.oswalker_state.walk()

				except StopIteration:
					self.current_state = self.STATES.UNRESOLVED_POSITIONAL
					logging.debug(
						f"[i:{self.counter}] OSWalker is collapsing. Setting state: {self.STATES.UNRESOLVED_POSITIONAL}")
					break

				# Try to pop a file from this walk frame
				try:
					logging.debug(f"[i:{self.counter}] Attempting to pop a file in this walk frame.")
					current_file = self.__resolve_to_relative_path(self.oswalker_state.current_oswalker_files.pop(0))

				except IndexError:
					logging.debug(f"[i:{self.counter}] No more OSWalker files available in this walk frame!")

		logging.debug(f"[i:{self.counter}] This walk is returning: {current_file}")
		return current_file

	def __fileext_filter_predicate__(self, filepath):
		"""Filter filenames by extension. Predicate filter for itertools."""
		skip_file = True
		for extension in self.file_extension_filters:
			if filepath.name.lower().endswith(extension):
				skip_file = False
				break
		return skip_file

	def __iter__(self):
		return self


class RC(Enum):
	"""Possible return codes of CLI application."""
	PASS = 0
	SYNTAX_ERR = 1


def parse_args(*args, **kwargs):
	"""Parse the arguments received from STDIN.
	param args: The string arguments to be parsed.
	return params: The arguments parsed into parameters.
	rtype: argparse.Namespace
	"""

	class _ArgumentParser(argparse.ArgumentParser):
		""" Supress exit and raise exceptions on syntax errors"""
		FLAG_HELP = "--help"

		def __init__(self, description):
			super().__init__(description=description, exit_on_error=False)

		def exit(self, status=0, message=None):
			if status:
				raise argparse.ArgumentError(argument=None, message=f"(status: {status}, message: '{message}'")

		def error(self, message):
			raise argparse.ArgumentError(argument=None, message=message)

	# Constructing argument parser
	parser = _ArgumentParser(description="* GCR Slicer |/-\\")
	parser.add_argument("positionals", type=str, nargs='+', help="A number of positional paths.")
	mutux = parser.add_mutually_exclusive_group()
	mutux.required = True  # Require a mutux option
	mutux.add_argument("--analyze", default=False, action='store_true', help="Analyze each file.")
	mutux.add_argument("--plot-audio", default=False, action='store_true', help="Plot each file.")
	mutux.add_argument("--write-dir", type=str, default=None, help="Path to write audio file slices.")
	parser.add_argument("-v", "--verbose", action="count", default=0, help="Amount of output during runtime.")
	parser.add_argument("--version", action='version', version=f"cli {__version__}")

	# Process and return parameters
	parsed_params = None
	try:
		parsed_params = parser.parse_args(*args, **kwargs)
	except argparse.ArgumentError as ae:
		if parser.FLAG_HELP not in list(*args):
			print(f"ArgumentError: {ae} (args: {list(*args)})", file=sys.stderr)

	return parsed_params


def plot_audio(audio_filename):
	"""Plot audio file with Matplotlib"""
	sample_rate, data = wavfile.read(audio_filename)
	duration = len(data) / sample_rate
	data_type = data.dtype
	amplitude_max = np.iinfo(data_type).max

	logging.info(f"Plotting audio_filename:'{audio_filename}'")
	logging.info(f"\tsample_rate:'{sample_rate}', duration:{duration}s, data_type:{data_type}")

	timeline = np.arange(0, duration, 1 / sample_rate)
	logging.info(f"\tlen(timeline):{len(timeline)}, timeline:{timeline}, ...")

	# Normalize amplitude to unit
	plot_data = data / amplitude_max

	plt.plot(timeline, plot_data)
	plt.xlabel('Time (s)')
	plt.ylabel(f"Amplitude ({data_type.name})")
	plt.ylim([-1, 1])
	plt.title(f"{audio_filename.name}")

	if data.ndim == 2:
		plt.legend(["Left channel", "Right channel"])

	plt.grid()
	plt.show()


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

	# Initialize filter iterator based on search paths and file extension filter.
	fpi = FileIterator(params.positionals, file_ext_filter=SUPPORTED_READ_EXTENSIONS)
	fpi = filterfalse(fpi.__fileext_filter_predicate__, fpi)

	# 'analyze', 'plot_audio', 'write_dir'
	if params.plot_audio:
		for file in fpi:
			plot_audio(file)
	elif params.analyze:
		pass
	elif params.write_dir:
		pass

	return 0


if __name__ == '__main__':
	main_params = parse_args(sys.argv[1:])
	sys.exit(main(main_params) if main_params else RC.SYNTAX_ERR.value)
