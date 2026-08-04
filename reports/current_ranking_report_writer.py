import csv
from pathlib import Path

OUTPUT_DIRECTORY = Path("reports") / "output"
OUTPUT_FILE = "current_rankings.csv"


class CurrentRankingReportWriter:

    def __init__(self):
        self.output_directory = OUTPUT_DIRECTORY
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(self, report):

        output_file = (
            self.output_directory
            / OUTPUT_FILE
        )

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.writer(csv_file)

            self._write_header(
                writer,
                report,
            )

            self._write_rows(
                writer,
                report,
            )

        return output_file

    def _write_header(
        self,
        writer,
        report,
    ):

        writer.writerow([
            "Trading Date",
            report.trading_date.date(),
        ])

        writer.writerow([])

        headers = [
            "Rank",
            "Symbol",
            "Score",
            "Avg Daily Traded Value",
        ]

        headers.extend(
            report.enabled_factors
        )

        writer.writerow(headers)

    def _write_rows(
        self,
        writer,
        report,
    ):

        for ranking in report.rankings:

            writer.writerow(
                self._build_row(
                    ranking,
                    report,
                )
            )

    def _build_row(
        self,
        ranking,
        report,
    ):

        row = [
            ranking.rank,
            ranking.stock.symbol,
            self._format(ranking.score, 4),
            self._format(
                ranking.stock.average_daily_traded_value,
                0,
            ),
        ]

        for factor_name in report.enabled_factors:
            row.append(
                self._format(
                    ranking.factor_values.get(factor_name),
                    2,
                )
            )

        return row

    def _format(self, value, digits=2):
        return round(value, digits)
