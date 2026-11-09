class FixedWidthParser:

    @staticmethod
    def record_type(line: str) -> str:
        return line[:4]

    @staticmethod
    def parse(line: str, structure: dict):

        row = {}

        for field in structure["fields"]:

            start = field["start"] - 1
            end = start + field["length"]

            row[field["name"]] = line[start:end]

        return row