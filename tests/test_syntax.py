import argparse
import unittest

from gcrslicer import parse_args


class TestGCRSlicerSyntax(unittest.TestCase):

	def test_help(self):
		self.assertIsNone(parse_args(['--help']))

	def test_badsyntax_null(self):
		self.assertIsNone(parse_args(['']))

	def test_badsyntax_no_positionals_some_good_options(self):
		self.assertIsNone(parse_args(['--analyze']))
		self.assertIsNone(parse_args(['--write-dir', '/tmp']))

	def test_badsyntax_some_positionals_no_options(self):
		self.assertIsNone(parse_args(['data/']))
		self.assertIsNone(parse_args(['data/', 'data2/', 'data3/']))

	def test_badsyntax_some_positionals_some_bad_options(self):
		self.assertIsNone(parse_args(['data/', 'data2/', 'data3/', '--analyze', '--write-dir', '/tmp']))
		self.assertIsNone(parse_args(['data/', 'data2/', 'data3/', '--write-dir', '/tmp', '--analyze']))

	def test_goodsytnax_some_positionals_some_good_options(self):
		params = parse_args(['data/', 'data2/', 'data3/', '--analyze'])
		self.assertIsNotNone(params)
		self.assertIsInstance(params, argparse.Namespace)
		params = parse_args(['data/', 'data2/', 'data3/', '--write-dir', '/tmp'])
		self.assertIsNotNone(params)
		self.assertIsInstance(params, argparse.Namespace)

