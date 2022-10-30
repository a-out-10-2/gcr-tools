from pathlib import Path
import unittest

from gcrslicer import FileIterator


class TestGCRFileIterator(unittest.TestCase):

	def test_empty(self):
		input_path_list = []  # must be strings
		expected_filelist = []

		fpi = FileIterator(input_path_list)
		found_filepaths = [filepath for filepath in fpi]
		self.assertListEqual(found_filepaths, expected_filelist, msg=f"Empty inputs (input_path_list:{input_path_list})"
																	 f" into FileIterator did not yield an empty list "
																	 f"(found_filepaths:{found_filepaths}).")

	def test_file(self):
		input_path_list = ['data2/anotherfile2.blr']  # must be strings
		expected_filelist = [Path('data2/anotherfile2.blr')]

		fpi = FileIterator(input_path_list)
		found_filepaths = [filepath for filepath in fpi]
		self.assertListEqual(found_filepaths, expected_filelist, msg=f"Inputs (input_path_list:{input_path_list})"
																	 f" into FileIterator did not yield (found_filepa"
																	 f"ths:{found_filepaths}) as expected (expected_"
																	 f"filelist:{expected_filelist}).")

	def test_dir(self):
		input_path_list = ['data2/']  # must be strings
		expected_filelist = [Path('data2/anotherfile2.blr'), Path('data2/somefile.blr')]

		fpi = FileIterator(input_path_list)
		found_filepaths = [filepath for filepath in fpi]
		self.assertListEqual(found_filepaths, expected_filelist, msg=f"Inputs (input_path_list:{input_path_list})"
																	 f" into FileIterator did not yield (found_filepa"
																	 f"ths:{found_filepaths}) as expected (expected_"
																	 f"filelist:{expected_filelist}).")


if __name__ == '__main__':
	unittest.main()
