from models.backtest_result import BacktestResult


class ConsoleReport:

    @staticmethod
    def print(result: BacktestResult):

        print()
        print("=" * 120)
        print("MONTHLY BACKTEST REPORT")
        print("=" * 120)

        for report in result.monthly_reports:

            print()

            print("-" * 120)
            print(
                f"Rebalance Date : {report.rebalance_date.strftime('%d-%b-%Y')}"
            )
            print(
                f"Execution Date : {report.execution_date.strftime('%d-%b-%Y')}"
            )
            print(
                f"Monthly Return : {report.monthly_return:.2%}"
            )
            print(
                f"Portfolio Value: {report.portfolio_value:.4f}"
            )
            print("-" * 120)

            print(
                f"{'Rank':<6}"
                f"{'Symbol':<18}"
                f"{'Score':>12}"
                f"{'Weight':>12}"
            )

            print("-" * 120)

            for position in report.portfolio.positions:

                print(
                    f"{position.rank:<6}"
                    f"{position.symbol:<18}"
                    f"{position.score:>12.4f}"
                    f"{position.weight:>11.2%}"
                )

        print()
        print("=" * 120)
        print("BACKTEST SUMMARY")
        print("=" * 120)

        metrics = result.metrics

        print(f"Total Return : {metrics.total_return:.2%}")
        print(f"CAGR         : {metrics.cagr:.2%}")
        print(f"Sharpe       : {metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown : {metrics.max_drawdown:.2%}")
        print(f"Win Rate     : {metrics.win_rate:.2%}")