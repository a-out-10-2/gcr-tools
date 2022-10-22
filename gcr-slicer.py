#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#   Copyright © <2022> Andrew Moe
# -----------------------------------------------------------------------------
import argparse
import logging
import webrtcvad
import sys

__version__ = 0.0

# Exportable API
__all__ = ['main', 'parse_args']


def parse_args(*args, **kwargs):
	"""Parse the arguments received from STDIN.
	param args: The string arguments to be parsed.
	return params: The arguments parsed into parameters.
	rtype: argparse.Namespace
	"""
	# Constructing argument parser
	parser = argparse.ArgumentParser(description="* GCR Slicer |/-\\")
	parser.add_argument("positionals", type=int, nargs='?', default=8, help="A number of positional paths.")
	mutux = parser.add_mutually_exclusive_group()
	mutux.add_argument("--analyze", default=False, action='store_true', help="Analyze and plot silence of each file.")
	mutux.add_argument("--write-dir", type=str, default=None, help="Path to write audio file slices.")
	parser.add_argument("-v", "--verbose", action="count", default=0, help="Amount of output during runtime.")
	parser.add_argument("--version", action='version', version='cli %s' % __version__)

	# Process and return parameters
	return parser.parse_args(*args, **kwargs)


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

	logging.debug("params: {}".format(params))
	logging.info("webrtcvad: {}".format(dir(webrtcvad)))

	return 0


if __name__ == '__main__':
	sys.exit(main(parse_args()))
