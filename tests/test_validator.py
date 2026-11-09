import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.validator import validate_file


class ValidatorSmokeTests(unittest.TestCase):
    def test_sample_file_validates_without_errors(self):
        report = validate_file(os.path.join(ROOT, "input", "sample_ifpa.txt"))
        self.assertEqual(report["summary"]["error_count"], 0)
        self.assertGreaterEqual(report["summary"]["record_count"], 1)

    def test_error_definition_is_loaded(self):
        from src.metadata import load_error_definitions

        errors = load_error_definitions()
        self.assertIn("BILAG5", errors)


if __name__ == "__main__":
    unittest.main()
