import pandas as pd


class ReportWriter:

    @staticmethod
    def write(errors, output_file):

        columns = {
            "line": "Line",
            "record_type": "Record",
            "field": "Field",
            "error": "Code",
            "message": "Description",
            "value": "Value",
        }
        df = pd.DataFrame.from_records(
            errors,
            columns=columns,
        ).rename(columns=columns)

        df.to_excel(
            output_file,
            index=False
        )