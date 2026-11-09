from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import load_workbook
import yaml

from src.metadata import MetadataLoader
from src.report import ReportWriter
from src.validator import validate_file


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = ROOT / "input" / "20260109_163204_IFPA2235-3RD.txt"


def sample_lines():
    return SAMPLE_FILE.read_text(encoding="latin-1").splitlines()


class ValidatorSmokeTests(unittest.TestCase):
    def test_sample_file_validates_without_errors(self):
        report = validate_file(SAMPLE_FILE)
        self.assertEqual(report["summary"]["error_count"], 0)
        self.assertEqual(report["summary"]["record_count"], 37)

    def test_sample_file_number_mismatch_is_reported(self):
        lines = sample_lines()
        header = lines[0]
        lines[0] = header[:12] + "0314326276" + header[22:]

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / SAMPLE_FILE.name
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        header_errors = [
            error
            for error in report["errors"]
            if error["line"] == 1 and error["field"] == "FILNR"
        ]
        self.assertEqual(len(header_errors), 1)
        self.assertEqual(header_errors[0]["error"], "PATTERN")

    def test_trailer_count_mismatch_is_reported(self):
        lines = sample_lines()
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

        self.assertIn(
            "TRAILER_COUNT_MISMATCH",
            {error["error"] for error in report["errors"]},
        )

    def test_nonblank_2235_filler_is_reported(self):
        lines = sample_lines()
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

        self.assertIn(
            ("FILLER_139", "FILLER_NOT_BLANK"),
            {(error["field"], error["error"]) for error in report["errors"]},
        )

    def test_final_period_marker_is_required(self):
        lines = sample_lines()
        lines[-1] = lines[-1][:-1] + " "

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "missing_marker.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        self.assertIn(
            ("FILLER_20", "TRAILER_MARKER"),
            {(error["field"], error["error"]) for error in report["errors"]},
        )

    def test_header_and_trailer_are_required(self):
        lines = sample_lines()
        content_without_boundaries = "\n".join(lines[1:-1]) + "\n"

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "missing_boundaries.txt"
            test_file.write_text(
                content_without_boundaries,
                encoding="latin-1",
            )
            report = validate_file(test_file)

        error_codes = {error["error"] for error in report["errors"]}
        self.assertIn("MISSING_HEADER", error_codes)
        self.assertIn("MISSING_TRAILER", error_codes)

    def test_header_and_trailer_must_be_file_boundaries(self):
        lines = sample_lines()
        lines[0], lines[1] = lines[1], lines[0]
        lines[-1], lines[-2] = lines[-2], lines[-1]

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "misordered_boundaries.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        error_codes = {error["error"] for error in report["errors"]}
        self.assertIn("INVALID_FIRST_RECORD", error_codes)
        self.assertIn("INVALID_LAST_RECORD", error_codes)

    def test_calendar_year_must_be_consistent_across_records(self):
        lines = sample_lines()
        second_data_record = list(lines[2])
        second_data_record[56:60] = "2024"
        lines[2] = "".join(second_data_record)

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "mixed_years.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        self.assertIn(
            "INCONSISTENT_FILE_VALUE",
            {error["error"] for error in report["errors"]},
        )

    def test_reporting_type_is_limited_and_consistent(self):
        lines = sample_lines()
        second_data_record = list(lines[2])
        second_data_record[1196] = "3"
        lines[2] = "".join(second_data_record)

        with TemporaryDirectory() as temporary_directory:
            test_file = Path(temporary_directory) / "invalid_report_type.txt"
            test_file.write_text(
                "\n".join(lines) + "\n",
                encoding="latin-1",
            )
            report = validate_file(test_file)

        self.assertIn(
            "ALLOWED_VALUE",
            {error["error"] for error in report["errors"]},
        )
        self.assertIn(
            "INCONSISTENT_FILE_VALUE",
            {error["error"] for error in report["errors"]},
        )

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
