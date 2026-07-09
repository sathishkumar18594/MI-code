import math

from models.backtest_metrics import (
    BacktestMetrics,
)
from models.backtest_result import (
    BacktestResult,
)


class MetricsService:

    def calculate(
        self,
        result: BacktestResult,
    ) -> BacktestMetrics:

        returns = [
            getattr(
                period.performance,
                "period_return",
                period.performance.portfolio_return,
            )
            for period in result.periods
        ]

        if not returns:

            return BacktestMetrics()

        metrics = BacktestMetrics()

        metrics.total_return = (
            self.total_return(
                returns
            )
        )

        metrics.cagr = self.cagr(
            returns
        )

        metrics.max_drawdown = (
            self.max_drawdown(
                returns
            )
        )

        metrics.win_rate = (
            self.win_rate(
                returns
            )
        )

        metrics.sharpe_ratio = (
            self.sharpe_ratio(
                returns
            )
        )

        metrics.annual_return = (
            metrics.cagr
        )

        return metrics

    def total_return(
        self,
        returns,
    ):

        equity = 1.0

        for value in returns:

            equity *= (
                1 + value
            )

        return equity - 1

    def cagr(
        self,
        returns,
    ):

        years = (
            len(returns)
            / 12
        )

        if years == 0:

            return 0.0

        total = (
            self.total_return(
                returns
            )
        )

        return (
            (1 + total)
            ** (1 / years)
            - 1
        )

    def max_drawdown(
        self,
        returns,
    ):

        equity = 1.0

        peak = 1.0

        drawdown = 0.0

        for value in returns:

            equity *= (
                1 + value
            )

            peak = max(
                peak,
                equity,
            )

            drawdown = min(
                drawdown,
                (
                    equity
                    - peak
                )
                / peak,
            )

        return abs(
            drawdown
        )

    def win_rate(
        self,
        returns,
    ):

        wins = sum(
            1
            for value in returns
            if value > 0
        )

        return (
            wins
            / len(returns)
        )

    def sharpe_ratio(
        self,
        returns,
        risk_free=0.0,
    ):

        if len(
            returns
        ) < 2:

            return 0.0

        average = (
            sum(returns)
            / len(returns)
        )

        variance = sum(

            (
                value
                - average
            ) ** 2

            for value in returns

        ) / (
            len(returns) - 1
        )

        std = math.sqrt(
            variance
        )

        if std == 0:

            return 0.0

        return (
            (
                average
                - risk_free
            )
            / std
        ) * math.sqrt(
            12
        )