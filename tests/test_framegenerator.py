"""Unit test module for the frame generator"""
from pathlib import Path
import unittest

from src.gcrslicer import SFFrameGenerator as FrameGenerator


@unittest.SkipTest
class TestGCRFrameGenerator(unittest.TestCase):
	"""Unit test methods for the frame generator"""

	def test_audiofile(self):
		"""Verify a frames of N-length can be taken from frame iterator"""
		input_filepath = Path('data-wav', '21 Tom Cat, Individual Meows.wav')
		# expected_filelist = None

		fg = FrameGenerator(input_filepath, 7)

		# self.assertListEqual(found_filelist, expected_filelist, msg=f"Inputs (input_path_list:{input_pathlist})"
		# 															f" into FileIterator did not yield (found_filelis"
		# 															f"t:{found_filelist}) as expected (expected_"
		# 															f"filelist:{expected_filelist}).")

		pass

	def test_dne_audiofile(self):
		pass


if __name__ == '__main__':
	unittest.main()
