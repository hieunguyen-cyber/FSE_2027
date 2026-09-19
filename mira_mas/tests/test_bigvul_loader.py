import csv
import tempfile
import unittest
from pathlib import Path
from mira_mas.data.bigvul_loader import load_bigvul_csv


class BigVulLoaderTests(unittest.TestCase):
    def test_raw_metadata_is_not_mistaken_for_function_level_data(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "raw.csv"
            source.write_text("project,commit_id,files_changed\nr,c,[]\n")
            with self.assertRaisesRegex(ValueError, "function-level"):
                list(load_bigvul_csv(source))

    def test_clean_record_is_oriented_as_reverse_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "clean.csv"
            source.write_text("id,project,commit_id,lang,func_before,func_after,cve_id,cwe_id,vul\n1,r,c,C,old,new,CVE-1,CWE-1,1\n")
            card = next(load_bigvul_csv(source))
            self.assertEqual(card.func_before, "old")
            self.assertEqual(card.func_after, "new")

    def test_non_vulnerable_function_is_excluded_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "clean.csv"
            source.write_text("id,project,commit_id,lang,func_before,func_after,vul\n1,r,c,C,old,new,0\n")
            self.assertEqual(list(load_bigvul_csv(source)), [])
