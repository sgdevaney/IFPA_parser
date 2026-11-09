import re


class Validator:

    def validate_record(
        self,
        line_number,
        line,
        structure
    ):
        errors = []

        expected_length = structure["record_length"]

        actual_length = len(line.rstrip("\n"))

        if actual_length != expected_length:
            errors.append(
                {
                    "line": line_number,
                    "field": "RECORD",
                    "error": "LENGTH",
                    "message": (
                        f"Expected {expected_length}, "
                        f"got {actual_length}"
                    )
                }
            )

        for field in structure["fields"]:

            start = field["start"] - 1
            end = start + field["length"]

            value = line[start:end]

            if field.get("required"):

                if not value.strip():

                    errors.append(
                        {
                            "line": line_number,
                            "field": field["name"],
                            "error": "REQUIRED",
                            "message": "Mandatory value missing"
                        }
                    )

            if field.get("datatype") == "numeric":

                stripped = value.strip()

                if stripped and not stripped.isdigit():

                    errors.append(
                        {
                            "line": line_number,
                            "field": field["name"],
                            "error": "NUMERIC",
                            "message": (
                                f"Not numeric: {value}"
                            )
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
                                "field": field["name"],
                                "error": "PATTERN",
                                "message": (
                                    f"Failed pattern {pattern}"
                                )
                            }
                        )

        return errors