import csv
import os
import sys
import unittest


@unittest.skipUnless(os.path.exists("vendor/bigvul/MSR_data_cleaned.csv"), "cleaned BigVul release is absent")
class BigVulIntegrationTests(unittest.TestCase):
    def test_real_cleaned_release_has_required_function_schema(self):
        csv.field_size_limit(sys.maxsize)
        with open("vendor/bigvul/MSR_data_cleaned.csv", encoding="utf-8", errors="replace", newline="") as stream:
            reader = csv.DictReader(stream)
            self.assertTrue({"func_before", "func_after", "vul", "patch"}.issubset(reader.fieldnames or []))
            first = next(reader)
        self.assertIn(first["vul"], {"0", "1"})
