import unittest
import os
from generated_metric import calculate

class TestCalculateMetrics(unittest.TestCase):
    def setUp(self):
        self.test_file = __file__
        self.test_repo = os.path.dirname(__file__)

    def test_basic_calculation(self):
        result = calculate(self.test_file)
        self.assertIsInstance(result, dict)
        self.assertIn('metrics', result)
        self.assertIn('benchmarks', result)
        self.assertIn('error', result)
        self.assertIsNone(result['error'])

    def test_invalid_file_path(self):
        result = calculate('/path/to/nonexistent/file.py')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['metrics'], {})
        self.assertEqual(result['benchmarks'], {})
        self.assertIn('File not found', result['error'])

    def test_with_repo_path(self):
        result = calculate(self.test_file, repo_path=self.test_repo)
        self.assertIsInstance(result, dict)
        self.assertIn('metrics', result)
        self.assertIn('benchmarks', result)
        self.assertTrue(any(metric in result['metrics'] for metric in [
            'num_authors', 'num_commits', 'bug_density', 'num_bugs',
            'pre_release_bugs', 'post_release_bugs', 'bug_fix_time',
            'defect_type', 'severity', 'priority'
        ]))

    def test_invalid_repo_path(self):
        result = calculate(self.test_file, repo_path='/invalid/repo/path')
        self.assertIsInstance(result, dict)
        self.assertIn('metrics', result)
        self.assertIn('Repository path not found', result['error'])

    def test_benchmark_generation(self):
        result = calculate(self.test_file, repo_path=self.test_repo)
        self.assertIn('benchmarks', result)
        self.assertTrue(any(benchmark in result['benchmarks'] for benchmark in ['defects4j', 'bugsjar']))

if __name__ == '__main__':
    unittest.main()