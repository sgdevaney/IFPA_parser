import argparse

from .report import ReportWriter
from .validator import validate_file


def main():
    parser = argparse.ArgumentParser(
        description="Validate an IFPA fixed-width file."
    )
    parser.add_argument("input_file")
    parser.add_argument(
        "--report",
        help="Write validation errors to an Excel workbook.",
    )
    args = parser.parse_args()
    report = validate_file(args.input_file)
    print(
        f"Validation complete. "
        f"{report['summary']['error_count']} errors found."
    )
    for error in report["errors"]:
        print(
            f"Line {error['line']}: {error['field']} "
            f"[{error['error']}] {error['message']}"
        )
    if args.report:
        ReportWriter.write(report["errors"], args.report)


if __name__ == "__main__":
    main()