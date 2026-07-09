

from pathlib import Path
import csv

OUTPUT_DIRECTORY = Path("reports") / "output"
OUTPUT_FILE = "current_portfolio.csv"

HEADERS = [
    "Rank",
    "Symbol",
    "Score",
    "Weight %",
    "Allocation",
    "Quantity",
    "Buy Price",
    "Current Price",
    "Market Value",
]


class CurrentPortfolioReportWriter:

    def __init__(self):
        self.output_directory = OUTPUT_DIRECTORY
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(
        self,
        report,
    ):

        output_file = (
            self.output_directory
            / OUTPUT_FILE
        )

        with output_file.open(
            "w",
            newline="",
        ) as file:

            writer = csv.writer(file)

            self._write_header(
                writer,
                report,
            )

            self._write_rows(
                writer,
                report,
            )

        return output_file

    def _write_header(self, writer, report):

        writer.writerow([
            "Trading Date",
            report.trading_date.date(),
        ])

        writer.writerow([])

        writer.writerow(HEADERS)

    def _write_rows(self, writer, report):

        for holding in report.portfolio.holdings:

            ranking = report.rank_lookup[holding.symbol]

            writer.writerow(
                self._build_row(
                    holding,
                    ranking,
                )
            )

    def _build_row(self, holding, ranking):

        return [
            ranking.rank,
            holding.symbol,
            self._format(ranking.stock.score, 4),
            self._format(holding.weight * 100, 2),
            self._format(holding.cost_value, 2),
            self._format(holding.quantity, 4),
            self._format(holding.entry_price, 2),
            self._format(holding.current_price, 2),
            self._format(holding.market_value, 2),
        ]

    def _format(self, value, digits=2):
        return round(value, digits)