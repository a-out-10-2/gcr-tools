import unittest

# from gcrslicer import parse_args, main
import gcrslicer


class TestGCRSlicerSyntax(unittest.TestCase):

	# TODO
	# gcr-slicer --help
	# gcr-slicer -vv --analyze
	# gcr-slicer -vv data/
	# gcr-slicer -vv data/ --analyze
	# gcr-slicer -vv data/ --write-dir /tmp
	# gcr-slicer -vv data/ data2/ data3/ --write-dir /tmp
	# gcr-slicer -vv data/ data2/ data7/ --write-dir /tmp
	# (!)gcr-slicer -vv data/ --write-dir /tmp --analyze
	# (!)gcr-slicer -vv data/ --write-dir /tmp --analyze

	def test_help(self):
		#self.assertEqual(True, False)  # add assertion here
		print("DBG: Entered test_help")

		# params = parse_args(['--help'])

		# print("DBG: params = {}".format(params))
		params = gcrslicer.parse_args("-vv --analyze")
		self.assertEqual(True, True)
