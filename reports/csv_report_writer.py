from pathlib import Path

import csv
from dataclasses import asdict, fields
from models.report.summary_report import SummaryReport
from models.report.monthly_report import MonthlyReport
from models.report.holding_report import HoldingReport
from models.report.annual_report import AnnualReport
from models.report.transaction_cost_report import TransactionCostReport
from models.report.metric_report import MetricReport
from models.report.decision_report import DecisionReport
from models.report.trade_report import TradeReport
from models.report.stock_summary_report import StockSummaryReport

from application.app_context import AppContext
from models.report.backtest_report import (
    BacktestReport,
)


class CsvReportWriter:

    def __init__(
        self,
        context: AppContext,
    ):

        self.context = context

        output = (
            context.config
            .get(
                "report",
                {},
            )
            .get(
                "output_directory",
                "reports/output",
            )
        )

        self.output_directory = Path(
            output
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(
        self,
        report: BacktestReport,
    ):
        """Write all report CSV files to the configured output directory."""

        self._write_summary(
            report
        )

        self._write_monthly(
            report
        )

        self._write_holdings(
            report
        )

        self._write_trades(
            report
        )

        self._write_annual(
            report
        )

        self._write_transaction_costs(
            report
        )

        self._write_metrics(
            report
        )

        self._write_decisions(
            report
        )
        self._write_stock_summary(report)
        self._write_monthly_return_matrix(
            report
        )

    def _write_csv(
        self,
        filename: str,
        model,
        rows,
    ):
        rows = list(rows)

        output_file = self.output_directory / filename

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            fieldnames = [
                field.name
                for field in fields(model)
            ]

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for row in rows:
                writer.writerow(asdict(row))

    def _write_single_csv(
        self,
        filename: str,
        model,
        row,
    ):

        output_file = self.output_directory / filename

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            fieldnames = [
                field.name
                for field in fields(model)
            ]

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            if row is not None:
                writer.writerow(asdict(row))

    def _write_summary(
        self,
        report: BacktestReport,
    ):
        self._write_single_csv("summary.csv", SummaryReport, report.summary)

    def _write_monthly(
        self,
        report: BacktestReport,
    ):
        self._write_csv("monthly.csv", MonthlyReport, report.monthly)

    def _write_holdings(
        self,
        report: BacktestReport,
    ):
        self._write_csv("holdings.csv", HoldingReport, report.holdings)

    def _write_trades(
        self,
        report: BacktestReport,
    ):
        self._write_csv("trades.csv", TradeReport, report.trades)

    def _write_annual(
        self,
        report: BacktestReport,
    ):
        self._write_csv("annual.csv", AnnualReport, report.annual)

    def _write_transaction_costs(
        self,
        report: BacktestReport,
    ):
        self._write_csv("transaction_costs.csv", TransactionCostReport, report.transaction_costs)

    def _write_metrics(
        self,
        report: BacktestReport,
    ):
        self._write_single_csv("metrics.csv", MetricReport, report.metrics)

    def _write_decisions(
        self,
        report: BacktestReport,
    ):
        self._write_csv("decisions.csv", DecisionReport, report.decisions)

    def _write_stock_summary(self, report: BacktestReport):
        self._write_csv(
            "stock_summary.csv",
            StockSummaryReport,
            report.stock_summary,
        )

    def _write_monthly_return_matrix(
        self,
        report: BacktestReport,
    ):

        output_file = (
            self.output_directory
            / "monthly_return_matrix.csv"
        )

        months = [
            "Year",
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=months,
            )

            writer.writeheader()

            for year, values in report.monthly_return_matrix.items():

                row = {"Year": year}

                row.update(values)

                writer.writerow(row)
