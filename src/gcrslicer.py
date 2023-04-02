#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#   Copyright © <2022> Andrew Moe
# -----------------------------------------------------------------------------
""" CLI utility for slicing audio files for SampleBrain."""
import argparse
from itertools import takewhile
from enum import Enum
import logging
import os
from pathlib import Path
import sys

from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt

# import webrtcvad

# Default supported extensions
SUPPORTED_READ_EXTENSIONS = {'wav'}  # , 'flac'}
# SUPPORTED_WRITE_EXTENSIONS = {'wav', 'aiff', 'aifc'}

__version__ = 0.0


def file_iterator(path_list: list, top=os.getcwd(), file_ext_filters=None):
	""" Create a file iterator based on a list of search paths.
	:param path_list: A list of paths (files, directories) for which to search for files.
	:param top: The top level directory to begin searching.
	:param file_ext_filters: A list of file extensions used to validate each file find. No filtering if None.
	:return: A generator returning files found withing the search paths
	:rtype: Path
	"""

	def __is_file_ext_valid(filepath: Path, extensions: list[str]):
		""" Verify if a file has an extension as specified by input.
		:param filepath: The file path to verify.
		:param extensions: A list of extension that validate a file path.
		:return: True if file path has a valid extension, False if not
		:rtype: bool
		"""
		matches_extension = True
		for extension in extensions:
			matches_extension = False
			if filepath.name.lower().endswith(extension):
				matches_extension = True
				break

		return matches_extension

	positionals = [Path(p) for p in path_list]
	file_extension_filters = file_ext_filters if file_ext_filters else []

	# Resolve each positional for file(s), until empty
	for positional in takewhile(lambda p: p is not None, positionals):

		# Skip positional, if it doesn't actually exist
		if not positional.exists:
			continue

		# Yield, if a valid file. Otherwise, skip
		if positional.is_file():
			if __is_file_ext_valid(positional, file_extension_filters):
				yield positional
			else:
				continue

		# Iterate over OS Walker for files, if a directory
		elif positional.is_dir():
			current_oswalker = \
				os.walk(os.path.join(top, positional.name), topdown=True, onerror=None, followlinks=True)

			# Yield, all files found in OSWalker
			for osw_root, _, osw_files in current_oswalker:
				for osw_file in osw_files:
					osw_pathfile = Path(osw_root).relative_to(top).joinpath(osw_file)

					# Yield, if a valid file. Otherwise, skip
					if __is_file_ext_valid(osw_pathfile, file_extension_filters):
						yield osw_pathfile
					else:
						continue

		else:
			print("Entered unknown \"file\" state.", file=sys.stderr)
			return

	return


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
	fpi = file_iterator(params.positionals, file_ext_filters=SUPPORTED_READ_EXTENSIONS)

	# 'analyze', 'plot_audio', 'write_dir'
	if params.plot_audio:
		for file in list(fpi):
			plot_audio(file)
	elif params.analyze:
		pass
	elif params.write_dir:
		pass

	return 0


if __name__ == '__main__':
	main_params = parse_args(sys.argv[1:])
	sys.exit(main(main_params) if main_params else RC.SYNTAX_ERR.value)
