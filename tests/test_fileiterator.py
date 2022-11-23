"""Unit test module for the FileIterator"""
import itertools
from pathlib import Path
import unittest

from gcrslicer import FileIterator


class TestGCRFileIterator(unittest.TestCase):
	"""Unit test methods for the FileIterator"""

	def test_empty(self):
		"""Verify an empty directory yields no files."""
		input_pathlist = []  # must be strings
		expected_filelist = []

		fpi = FileIterator(input_pathlist)
		found_filelist = list(fpi)
		self.assertListEqual(found_filelist, expected_filelist, msg=f"Empty inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield an empty list "
																	f"(found_filelist:{found_filelist}).")

	def test_file(self):
		"""Verify a file search path yields one file."""
		input_pathlist = ['data2/anotherfile2.blr']  # must be strings
		expected_filelist = [Path('data2/anotherfile2.blr')]

		fpi = FileIterator(input_pathlist)
		found_filelist = list(fpi)
		self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield (found_filelis"
																	f"t:{found_filelist}) as expected (expected_"
																	f"filelist:{expected_filelist}).")

	def test_dir(self):
		"""Verify files are found withing directory."""
		input_pathlist = ['data2/']  # must be strings
		expected_filelist = [Path('data2/anotherfile2.blr'), Path('data2/somefile.blr')]

		fpi = FileIterator(input_pathlist)
		found_filelist = list(fpi)

		self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield (found_filelis"
																	f"t:{found_filelist}) as expected (expected_"
																	f"filelist:{expected_filelist}).")

	def test_deep_dir(self):
		"""Verify files are found withing directory."""
		input_pathlist = ['data3/']  # must be strings
		expected_filelist = [Path('data3/oldaudio.mp1'),
							 Path('data3/gabbaghoul/freshmeat.eat'),
							 Path('data3/gabbaghoul/rottenm-eats.tar.xz'),
							 Path('data3/gabbaghoul/littlepeppercorns/thatonethere.gps3'),
							 Path('data3/gabbaghoul/littlepeppercorns/thisonehere.gps')]

		fpi = FileIterator(input_pathlist)
		found_filelist = list(fpi)

		self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield (found_filelis"
																	f"t:{found_filelist}) as expected (expected_"
																	f"filelist:{expected_filelist}).")

	def test_file_dir(self):
		"""Verify search paths can be resolved to files."""
		input_pathlist = ['data3/oldaudio.mp1', 'data2/']  # must be strings
		expected_filelist = [Path('data3/oldaudio.mp1'), Path('data2/anotherfile2.blr'), Path('data2/somefile.blr')]

		fpi = FileIterator(input_pathlist)
		found_filelist = list(fpi)

		self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield (found_filelis"
																	f"t:{found_filelist}) as expected (expected_"
																	f"filelist:{expected_filelist}).")

	def test_dir_file(self):
		"""Verify search paths can be resolved to files."""
		input_pathlist = ['data2/', 'data3/oldaudio.mp1']  # must be strings
		expected_filelist = [Path('data2/anotherfile2.blr'), Path('data2/somefile.blr'), Path('data3/oldaudio.mp1')]

		fpi = FileIterator(input_pathlist)
		found_filelist = list(fpi)

		self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield (found_filelis"
																	f"t:{found_filelist}) as expected (expected_"
																	f"filelist:{expected_filelist}).")

	def test_file_extension_filter(self):
		"""Verify file iterator elements can be filtered by file extension."""
		input_pathlist = ['data3/']  # must be strings
		extension_filter = ['.gps', '.gps3']
		expected_filelist = [
			Path('data3/gabbaghoul/littlepeppercorns/thatonethere.gps3'),
			Path('data3/gabbaghoul/littlepeppercorns/thisonehere.gps')
		]

		fpi = FileIterator(input_pathlist, file_ext_filter=extension_filter)
		fpi_filtered = itertools.filterfalse(fpi.__fileext_filter_predicate__, fpi)
		found_filelist = list(fpi_filtered)

		self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
																	f" into FileIterator did not yield (found_filelis"
																	f"t:{found_filelist}) as expected (expected_"
																	f"filelist:{expected_filelist}).")


if __name__ == '__main__':
	unittest.main()
