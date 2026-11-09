import pandas as pd


class ReportWriter:

    @staticmethod
    def write(errors, output_file):

        df = pd.DataFrame(errors)

        df.to_excel(
            output_file,
            index=False
        )