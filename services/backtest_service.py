from copy import deepcopy
from models.backtest_period import (
    BacktestPeriod,
)
from models.backtest_result import (
    BacktestResult,
)
from models.portfolio_state import (
    PortfolioState,
)
from services.market_filter_service import (
    MarketFilterService,
)
from services.performance_service import (
    PerformanceService,
)
from services.metrics_service import (
    MetricsService,
)
from services.report_builder import (
    ReportBuilder,
)
from reports.csv_report_writer import (
    CsvReportWriter,
)
from services.portfolio_manager import (
    PortfolioManager,
)
from services.ranking_service import (
    RankingService,
)
from application.app_context import AppContext


class BacktestService:

    def __init__(
        self,
        context: AppContext,
    ):

        self.context = context

        self.market_filter = (
            MarketFilterService(
                context
            )
        )

        self.ranking_service = (
            RankingService(
                context
            )
        )
        self.portfolio_manager = (
            PortfolioManager(
                context
            )
        )

        self.performance_service = (
            PerformanceService(
                context
            )
        )

        self.metrics_service = (
            MetricsService()
        )

        self.report_builder = (
            ReportBuilder(
                context
            )
        )

        self.csv_report_writer = (
            CsvReportWriter(
                context
            )
        )

    def run(
        self,
        symbols,
        trading_dates,
        rebalance_dates,
    ) -> BacktestResult:

        periods = []

        state = PortfolioState(
            cash=self.context.config["portfolio"]["initial_capital"],
        )
        previous_ending_value = (
            self.context.config["portfolio"]["initial_capital"]
        )
        rebalance_dates_set = set(rebalance_dates)
        self.ranking_service.build_cache(
            symbols=symbols,
            trading_dates=trading_dates,
        )
        for index in range(len(trading_dates) - 1):

            trading_date = trading_dates[index]
            exit_date = trading_dates[index + 1]

            state, period, previous_ending_value = (
                self.execute_day(
                    state=state,
                    trading_date=trading_date,
                    exit_date=exit_date,
                    previous_ending_value=previous_ending_value,
                    is_rebalance_day=(trading_date in rebalance_dates_set),
                )
            )

            periods.append(period)

        result = BacktestResult(
            periods=periods,
            metrics=None,
        )

        result.metrics = (
            self.metrics_service.calculate(
                result
            )
        )

        report = (
            self.report_builder.build(
                result
            )
        )

        self.csv_report_writer.write(
            report
        )

        return result

    def execute_day(
        self,
        state,
        trading_date,
        exit_date,
        previous_ending_value,
        is_rebalance_day,
    ):

        market_bullish = (
            self.market_filter.is_bullish(
                trading_date
            )
        )

        rankings = (
            self.ranking_service.get_rankings(
                trading_date
            )
        )
        state = (
            self.portfolio_manager.update(
                state=state,
                rankings=rankings,
                market_bullish=market_bullish,
                rebalance_date=trading_date,
                is_rebalance_day=is_rebalance_day,
            )
        )
        state.portfolio.rebalance_date = (
            trading_date
        )
        # Preserve the entry snapshot and attach the exit valuation for reporting.
        period_portfolio = deepcopy(
            state.portfolio
        )

        performance = (
            self.performance_service.calculate(
                portfolio=state.portfolio,
                beginning_value=previous_ending_value,
                entry_signal_date=trading_date,
                exit_signal_date=exit_date,
            )
        )
        period_portfolio.invested_value = (
            performance.ending_value
            - period_portfolio.cash
        )
        period_portfolio.total_value = (
            performance.ending_value
        )
        period_portfolio.unrealized_pnl = (
            performance.unrealized_pnl
        )
        period_portfolio.realized_pnl = (
            performance.realized_pnl
        )

        previous_ending_value = (
            performance.ending_value
        )

        return (
            state,
            BacktestPeriod(
                portfolio=period_portfolio,
                performance=performance,
            ),
            previous_ending_value,
        )

    def _process_day(
        self,
        state,
        symbols,
        trading_date,
        exit_date,
        previous_ending_value,
        is_rebalance_day,
    ):
        return self.execute_day(
            state=state,
            trading_date=trading_date,
            exit_date=exit_date,
            previous_ending_value=previous_ending_value,
            is_rebalance_day=is_rebalance_day,
        )