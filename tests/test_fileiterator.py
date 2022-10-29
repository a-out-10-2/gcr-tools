from pathlib import Path
import unittest

from gcrslicer import FileIterator


class TestGCRFileIterator(unittest.TestCase):

	def test_something(self):
		expected_filelist = [Path(), Path()]
		input_path_list = []  # must be strings
		fpi = FileIterator(input_path_list)
		filepaths = [filepath for filepath in fpi]

		self.assertListEqual(filepaths, expected_filelist)


if __name__ == '__main__':
	unittest.main()
