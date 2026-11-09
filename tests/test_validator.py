from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import load_workbook
import yaml

from src.metadata import MetadataLoader
from src.report import ReportWriter
from src.validator import validate_file


ROOT = Path(__file__).resolve().parent.parent


class ValidatorSmokeTests(unittest.TestCase):
    def test_sample_file_validates_without_errors(self):
        sample = ROOT / "input" / "20260109_163204_IFPA2235-3RD.txt"
        report = validate_file(sample)
        self.assertEqual(report["summary"]["error_count"], 0)
        self.assertEqual(report["summary"]["record_count"], 37)

    def test_trailer_count_mismatch_is_reported(self):
        sample = ROOT / "input" / "20260109_163204_IFPA2235-3RD.txt"
        lines = sample.read_text(encoding="latin-1").splitlines()
        trailer_index = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("9998")
        )
        trailer = lines[trailer_index]
        lines[trailer_index] = (
            trailer[:12] + "0000036" + trailer[19:]
        )

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "trailer_mismatch.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        self.assertEqual(report["summary"]["error_count"], 1)
        self.assertEqual(
            report["errors"][0]["error"],
            "TRAILER_COUNT_MISMATCH",
        )

    def test_nonblank_2235_filler_is_reported(self):
        sample = ROOT / "input" / "20260109_163204_IFPA2235-3RD.txt"
        lines = sample.read_text(encoding="latin-1").splitlines()
        data_record = list(lines[1])
        data_record[138] = "X"
        lines[1] = "".join(data_record)

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "nonblank_filler.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        self.assertEqual(report["summary"]["error_count"], 1)
        self.assertEqual(report["errors"][0]["field"], "FILLER_139")
        self.assertEqual(report["errors"][0]["error"], "FILLER_NOT_BLANK")

    def test_final_period_marker_is_required(self):
        sample = ROOT / "input" / "20260109_163204_IFPA2235-3RD.txt"
        lines = sample.read_text(encoding="latin-1").splitlines()
        lines[-1] = lines[-1][:-1] + " "

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "missing_marker.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        self.assertEqual(report["summary"]["error_count"], 1)
        self.assertEqual(report["errors"][0]["field"], "FILLER_20")
        self.assertEqual(report["errors"][0]["error"], "TRAILER_MARKER")

    def test_excel_report_has_expected_columns(self):
        columns = [
            "line",
            "record_type",
            "field",
            "error",
            "message",
            "value",
        ]
        errors = [
            {
                "line": 37,
                "record_type": "9998",
                "field": "record_count",
                "error": "TRAILER_COUNT_MISMATCH",
                "message": "Count does not match",
                "value": "0000036",
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.xlsx"
            ReportWriter.write(errors, report_path)

            workbook = load_workbook(report_path, read_only=True)
            headers = list(
                next(workbook.active.iter_rows(values_only=True))
            )
            workbook.close()

        self.assertEqual(
            headers,
            ["Line", "Record", "Field", "Code", "Description", "Value"],
        )

    def test_bilag5_catalogue_contains_errors_and_advisories(self):
        catalogue_path = ROOT / "data" / "errors" / "bilag5.yaml"
        catalogue = yaml.safe_load(
            catalogue_path.read_text(encoding="utf-8")
        )
        entries = catalogue["errors"]

        self.assertEqual(len(entries), 116)
        self.assertEqual(entries["024"]["severity"], "error")
        self.assertEqual(entries["599"]["severity"], "ok")
        self.assertEqual(entries["801"]["severity"], "advisory")
        self.assertIn("correction", entries["024"])
        self.assertEqual(
            sum(entry["severity"] == "error" for entry in entries.values()),
            109,
        )
        self.assertEqual(
            sum(
                entry["severity"] == "advisory"
                for entry in entries.values()
            ),
            6,
        )

    def test_2235_schema_covers_the_entire_fixed_width_record(self):
        loader = MetadataLoader(ROOT / "data" / "structures")
        structure = loader.load_structure("2235")
        position = 1

        for field in structure["fields"]:
            self.assertEqual(field["start"], position, field["name"])
            position += field["length"]

        self.assertEqual(len(structure["fields"]), 83)
        self.assertEqual(position, 1347)


if __name__ == "__main__":
    unittest.main()
