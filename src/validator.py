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

            allowed_values = field.get("allowed_values")
            if (
                allowed_values is not None
                and value.strip()
                and value.strip() not in allowed_values
            ):
                errors.append(
                    {
                        "line": line_number,
                        "record_type": record_type,
                        "field": field["name"],
                        "error": "ALLOWED_VALUE",
                        "message": (
                            f"Expected one of {', '.join(allowed_values)}"
                        ),
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
    record_types = [line[:4] for line in lines]
    consistent_values = {}

    for record_type, position in (("0001", "first"), ("9998", "last")):
        matching_lines = [
            line_number
            for line_number, current_type in enumerate(record_types, start=1)
            if current_type == record_type
        ]
        if not matching_lines:
            errors.append(
                {
                    "line": 1 if position == "first" else max(1, len(lines)),
                    "record_type": record_type,
                    "field": "RECORD",
                    "error": f"MISSING_{'HEADER' if position == 'first' else 'TRAILER'}",
                    "message": f"Required {position} record {record_type} is missing",
                    "value": "",
                }
            )
            continue

        if len(matching_lines) > 1:
            for line_number in matching_lines[1:]:
                errors.append(
                    {
                        "line": line_number,
                        "record_type": record_type,
                        "field": "RECORD",
                        "error": "DUPLICATE_BOUNDARY_RECORD",
                        "message": (
                            f"Record {record_type} may occur only once"
                        ),
                        "value": lines[line_number - 1],
                    }
                )

        expected_line = 1 if position == "first" else len(lines)
        if matching_lines[0] != expected_line:
            errors.append(
                {
                    "line": matching_lines[0],
                    "record_type": record_type,
                    "field": "RECORD",
                    "error": f"INVALID_{position.upper()}_RECORD",
                    "message": (
                        f"Record {record_type} must be the {position} "
                        f"record (line {expected_line})"
                    ),
                    "value": lines[matching_lines[0] - 1],
                }
            )

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

        for field in structure["fields"]:
            if not field.get("consistent_across_file"):
                continue
            start = field["start"] - 1
            end = start + field["length"]
            value = line[start:end].strip()
            if not value:
                continue

            key = (record_type, field["name"])
            first_value = consistent_values.setdefault(key, value)
            if value != first_value:
                errors.append(
                    {
                        "line": line_number,
                        "record_type": record_type,
                        "field": field["name"],
                        "error": "INCONSISTENT_FILE_VALUE",
                        "message": (
                            f"Value must match {first_value!r} throughout "
                            "the file"
                        ),
                        "value": value,
                    }
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