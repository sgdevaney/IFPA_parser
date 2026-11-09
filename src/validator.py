import re
from pathlib import Path

from .metadata import MetadataLoader


class Validator:

    def validate_record(
        self,
        line_number,
        line,
        structure
    ):
        errors = []
        record_type = structure.get("record_type", line[:4])

        expected_length = structure["record_length"]

        actual_length = len(line.rstrip("\n"))

        if actual_length != expected_length:
            errors.append(
                {
                    "line": line_number,
                    "record_type": record_type,
                    "field": "RECORD",
                    "error": "LENGTH",
                    "message": (
                        f"Expected {expected_length}, "
                        f"got {actual_length}"
                    ),
                    "value": "",
                }
            )

        for field in structure["fields"]:

            start = field["start"] - 1
            end = start + field["length"]

            value = line[start:end]

            if field.get("blank") and value.strip():
                errors.append(
                    {
                        "line": line_number,
                        "record_type": record_type,
                        "field": field["name"],
                        "error": "FILLER_NOT_BLANK",
                        "message": "Filler field must be blank",
                        "value": value,
                    }
                )

            if "trailing_marker" in field:
                marker = field["trailing_marker"]
                if (
                    not value.endswith(marker)
                    or value[:-len(marker)].strip()
                ):
                    errors.append(
                        {
                            "line": line_number,
                            "record_type": record_type,
                            "field": field["name"],
                            "error": "TRAILER_MARKER",
                            "message": (
                                f"Filler field must contain only blanks "
                                f"followed by {marker!r}"
                            ),
                            "value": value,
                        }
                    )

            if field.get("required"):

                if not value.strip():

                    errors.append(
                        {
                            "line": line_number,
                            "record_type": record_type,
                            "field": field["name"],
                            "error": "REQUIRED",
                            "message": "Mandatory value missing",
                            "value": value,
                        }
                    )

            if field.get("datatype") == "numeric":

                stripped = value.strip()

                if stripped and not stripped.isdigit():

                    errors.append(
                        {
                            "line": line_number,
                            "record_type": record_type,
                            "field": field["name"],
                            "error": "NUMERIC",
                            "message": (
                                f"Not numeric: {value}"
                            ),
                            "value": value,
                        }
                    )

            pattern = field.get("pattern")

            if pattern:

                if value.strip():

                    if not re.fullmatch(
                        pattern,
                        value.strip()
                    ):
                        errors.append(
                            {
                                "line": line_number,
                                "record_type": record_type,
                                "field": field["name"],
                                "error": "PATTERN",
                                "message": (
                                    f"Failed pattern {pattern}"
                                ),
                                "value": value,
                            }
                        )

        return errors

    def validate_trailer_count(
        self,
        line_number,
        line,
        structure,
        actual_record_count,
    ):
        field_name = structure["record_count_field"]
        field = next(
            (
                field
                for field in structure["fields"]
                if field["name"] == field_name
            ),
            None,
        )
        if field is None:
            raise ValueError(
                f"Record count field {field_name!r} is not defined"
            )
        start = field["start"] - 1
        end = start + field["length"]
        count = line[start:end].strip()

        if not count.isdigit():
            return []

        expected_record_count = int(count)
        if expected_record_count == actual_record_count:
            return []

        return [
            {
                "line": line_number,
                "record_type": structure["record_type"],
                "field": field_name,
                "error": "TRAILER_COUNT_MISMATCH",
                "message": (
                    f"Trailer declares {expected_record_count} records, "
                    f"but the file contains {actual_record_count}"
                ),
                "value": count,
            }
        ]


def validate_file(file_path, structures_directory=None):
    file_path = Path(file_path)
    if structures_directory is None:
        structures_directory = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "structures"
        )

    metadata = MetadataLoader(structures_directory)
    validator = Validator()
    errors = []
    lines = file_path.read_text(encoding="latin-1").splitlines()

    for line_number, line in enumerate(lines, start=1):
        record_type = line[:4]

        try:
            structure = metadata.load_structure(record_type)
        except FileNotFoundError:
            errors.append(
                {
                    "line": line_number,
                    "record_type": record_type,
                    "field": "RECORD",
                    "error": "UNKNOWN_RECORD_TYPE",
                    "message": f"Unknown record type: {record_type}",
                    "value": line,
                }
            )
            continue

        if "record_length" not in structure or any(
            "start" not in field or "length" not in field
            for field in structure.get("fields", [])
        ):
            errors.append(
                {
                    "line": line_number,
                    "record_type": record_type,
                    "field": "RECORD",
                    "error": "INVALID_STRUCTURE",
                    "message": (
                        f"Structure {record_type} is missing "
                        "record length or field positions"
                    ),
                    "value": line,
                }
            )
            continue

        errors.extend(
            validator.validate_record(
                line_number,
                line,
                structure,
            )
        )

        if "record_count_field" in structure:
            excluded_record_types = set(
                structure.get("record_count_excluded_types", [])
            )
            counted_record_count = sum(
                1
                for record in lines
                if record[:4] not in excluded_record_types
            )
            errors.extend(
                validator.validate_trailer_count(
                    line_number,
                    line,
                    structure,
                    counted_record_count,
                )
            )

    return {
        "errors": errors,
        "summary": {
            "record_count": len(lines),
            "error_count": len(errors),
        },
    }