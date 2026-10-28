# Created by 11Hopem
# Copyright (c) 2026 11Hopem. All rights reserved.
# Licensed under 11Hopem Proprietary License.

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from src.cloud_logger.logger import CloudLogger

class TestCloudLogger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = Path(self.test_dir)
        self.logger = CloudLogger(project_name="test-project", log_dir=self.log_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_logger_initialization(self):
        self.assertEqual(self.logger.config.project_name, "test-project")
        self.assertTrue(self.log_path.exists())

    def test_info_logging_writes_locally(self):
        self.logger.info("Test info message", context={"key1": "val1"})
        app_jsonl = self.logger.storage.app_jsonl
        self.assertTrue(app_jsonl.exists())
        with open(app_jsonl, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["level"], "INFO")
        self.assertEqual(lines[0]["message"], "Test info message")
        self.assertEqual(lines[0]["context"]["key1"], "val1")

    def test_error_logging_with_exception(self):
        try:
            raise ValueError("Test error exception")
        except ValueError as e:
            self.logger.error("Error occurred", error=e, context={"action": "test"})
        error_jsonl = self.logger.storage.error_jsonl
        self.assertTrue(error_jsonl.exists())
        with open(error_jsonl, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["level"], "ERROR")
        self.assertIn("Test error exception", lines[0].get("traceback", ""))

    def test_zero_crash_on_invalid_data(self):
        # Should not crash on empty strings or special characters
        self.logger.warning("Warning message", context={"special": "çöşğüı"})
        app_jsonl = self.logger.storage.app_jsonl
        self.assertTrue(app_jsonl.exists())

if __name__ == "__main__":
    unittest.main()
