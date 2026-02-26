from generated_metric import calculate
import unittest
import os
import tempfile


class TestCalculateMetrics(unittest.TestCase):
    def setUp(self):
        self.test_file = __file__
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_path, exist_ok=True)

    def test_basic_calculation(self):
        result = calculate(self.test_file)
        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertIn("benchmarks", result)
        self.assertIn("error", result)
        
    def test_invalid_file_path(self):
        result = calculate("nonexistent_file.py")
        self.assertIsInstance(result, dict)
        self.assertTrue(result["error"].startswith("File not found"))
        self.assertEqual(result["metrics"], {})
        self.assertEqual(result["benchmarks"], {})

    def test_with_repo_path(self):
        result = calculate(self.test_file, repo_path=self.repo_path)
        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertIn("benchmarks", result)
        
    def test_with_invalid_repo_path(self):
        result = calculate(self.test_file, repo_path="nonexistent_repo")
        self.assertIsInstance(result, dict)
        self.assertTrue(result["error"].startswith("Repository path not found"))

    def test_metrics_keys(self):
        result = calculate(self.test_file)
        expected_metrics = {
            'num_authors', 'num_commits', 'bug_density', 'num_bugs',
            'pre_release_bugs', 'post_release_bugs', 'bug_fix_time',
            'defect_type', 'severity', 'priority'
        }
        self.assertTrue(
            all(key in expected_metrics for key in result["metrics"].keys())
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    unittest.main()