
from models.backtest_result import BacktestResult


class ReportService:

    def build_monthly_return_matrix(
        self,
        result: BacktestResult,
    ):

        months = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]

        matrix = {}

        previous_value = None

        for period in result.periods:

            portfolio = period.portfolio
            date = portfolio.rebalance_date
            current_value = portfolio.total_value

            year = date.year
            month = date.strftime("%b")

            if year not in matrix:
                matrix[year] = {m: None for m in months}

            if previous_value is None or previous_value <= 0:
                monthly_return = 0.0
            else:
                monthly_return = (
                    (current_value - previous_value)
                    / previous_value
                )

            matrix[year][month] = round(
                monthly_return * 100,
                2,
            )

            previous_value = current_value

        return matrix