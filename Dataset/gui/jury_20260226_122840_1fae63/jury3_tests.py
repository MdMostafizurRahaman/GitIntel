import unittest
import os
from generated_metric import calculate

class TestBugMetricsCalculator(unittest.TestCase):
    def setUp(self):
        self.test_file_path = __file__
        self.fake_repo_path = "non_existent_repo"
        self.valid_repo_path = os.path.dirname(__file__)

    def test_basic_calculation(self):
        result = calculate(self.test_file_path)
        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertIn("benchmarks", result)
        self.assertIn("error", result)
        self.assertIsNone(result["error"])

    def test_invalid_file_path(self):
        result = calculate("non_existent_file.py")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["metrics"], {})
        self.assertEqual(result["benchmarks"], {})
        self.assertIsNotNone(result["error"])
        self.assertTrue("File not found" in result["error"])

    def test_invalid_repo_path(self):
        result = calculate(self.test_file_path, repo_path=self.fake_repo_path)
        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertEqual(result["benchmarks"], {})
        self.assertIsNotNone(result["error"])
        self.assertTrue("Repository path not found" in result["error"])

    def test_with_valid_repo(self):
        result = calculate(self.test_file_path, repo_path=self.valid_repo_path)
        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertIn("benchmarks", result)
        self.assertIsNone(result["error"])

    def test_metrics_keys(self):
        result = calculate(self.test_file_path)
        expected_metrics = {
            'num_authors', 'num_commits', 'bug_density', 'num_bugs',
            'pre_release_bugs', 'post_release_bugs', 'bug_fix_time',
            'defect_type', 'severity', 'priority'
        }
        self.assertTrue(all(key in expected_metrics for key in result["metrics"].keys()))

if __name__ == '__main__':
    unittest.main()