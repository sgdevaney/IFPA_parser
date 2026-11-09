from pathlib import Path

from metadata import MetadataLoader
from validator import Validator


def main():

    metadata = MetadataLoader(
        "../data/structures"
    )

    validator = Validator()

    errors = []

    file_name = (
        "input/"
        "20260109_163204_IFPA2235-3RD.txt"
    )

    with open(
        file_name,
        encoding="latin-1"
    ) as fh:

        for line_no, line in enumerate(fh, start=1):

            record_type = line[:4]

            try:
                structure = metadata.load_structure(
                    record_type
                )
            except FileNotFoundError:
                continue

            errors.extend(
                validator.validate_record(
                    line_no,
                    line.rstrip("\n"),
                    structure
                )
            )

    print(
        f"Validation complete. "
        f"{len(errors)} errors found."
    )


if __name__ == "__main__":
    main()