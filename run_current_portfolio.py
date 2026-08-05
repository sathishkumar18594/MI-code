from datetime import datetime
import pandas as pd
import csv
from pathlib import Path
from bootstrap import Bootstrap
from services.universe_service import UniverseService
from services.market_filter_service import MarketFilterService
from services.ranking_service import RankingService
from services.current_portfolio_report_builder import CurrentPortfolioReportBuilder
from reports.current_ranking_report_writer import CurrentRankingReportWriter
from services.current_ranking_report_builder import CurrentRankingReportBuilder
from reports.current_portfolio_report_writer import CurrentPortfolioReportWriter
from services.portfolio_manager import PortfolioManager
from models.portfolio_state import PortfolioState
from services.backtest_service import BacktestService


def main():
    bootstrap = Bootstrap()
    context = bootstrap.context
    calendar = bootstrap.signal_calendar_service()

    market_filter = MarketFilterService(
        context
    )

    ranking_service = RankingService(
        context
    )

    portfolio_manager = PortfolioManager(
        context
    )

    report_builder = CurrentPortfolioReportBuilder()
    ranking_report_builder = CurrentRankingReportBuilder(
        ranking_service.scoring_service,
    )
    ranking_report_writer = CurrentRankingReportWriter()
    portfolio_report_writer = CurrentPortfolioReportWriter()

    universe = UniverseService()

    universe_name = context.config[
        "universe"
    ]["name"]

    symbols = universe.get_universe(
        universe_name.lower()
    )

    latest_date = (
        context.price_repository.latest_trading_date()
    )

    trading_dates = [latest_date]

    ranking_service.build_cache(
        symbols=symbols,
        trading_dates=trading_dates,
    )

    market_bullish = (
        market_filter.is_bullish(
            latest_date
        )
    )

    if not market_bullish:
        print(
            f"Market is bearish on "
            f"{latest_date.date()}. "
            f"No portfolio generated."
        )
        return

    initial_signal_date = pd.Timestamp(
        context.config["live_tracking"]["initial_signal_date"]
    )
    tracking_dates = calendar.trading_dates(initial_signal_date, latest_date)
    replay = BacktestService(context).run(
        symbols=symbols,
        trading_dates=tracking_dates,
        rebalance_dates=calendar.signal_dates(initial_signal_date, latest_date),
        write_reports=False,
    )
    portfolio = replay.periods[-1].portfolio

    rankings = ranking_service.get_rankings(
        latest_date
    )
    entry_rankings = ranking_service.get_entry_rankings(latest_date)

    ranking_report = ranking_report_builder.build(
        trading_date=latest_date,
        rankings=entry_rankings,
    )

    ranking_output_file = ranking_report_writer.write(
        ranking_report
    )

    report = report_builder.build(
        trading_date=latest_date,
        portfolio=portfolio,
        rankings=entry_rankings,
    )

    portfolio_output_file = (
        portfolio_report_writer.write(
            report
        )
    )

    execution_date = calendar.next_trading_date(latest_date)
    sell_rank = max(1, int(len(rankings) * 0.10))
    rank_lookup = {ranking.stock.symbol: ranking for ranking in rankings}
    actions = []
    for holding in portfolio.holdings:
        ranking = rank_lookup.get(holding.symbol)
        if ranking is None or ranking.rank > sell_rank:
            actions.append([
                "SELL", holding.symbol,
                ranking.rank if ranking else "Not ranked",
                execution_date.date(), "Rank exit",
            ])

    signal_dates = set(calendar.signal_dates(latest_date, latest_date))
    if latest_date in signal_dates:
        held_after_sells = {
            holding.symbol for holding in portfolio.holdings
            if holding.symbol not in {action[1] for action in actions}
        }
        for ranking in entry_rankings:
            if len(held_after_sells) >= context.config["strategy"]["portfolio_size"]:
                break
            if ranking.stock.symbol in held_after_sells:
                continue
            actions.append([
                "BUY", ranking.stock.symbol, ranking.rank,
                execution_date.date(), "Monthly replacement",
            ])
            held_after_sells.add(ranking.stock.symbol)

    actions_file = Path("reports/output/current_actions.csv")
    with actions_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Action", "Symbol", "Rank", "Scheduled execution", "Reason"])
        writer.writerows(actions)

    print()
    print("=" * 60)
    print("Current Portfolio Generated Successfully")
    print(f"Trading Date : {latest_date.date()}")
    print(f"Rankings File : {ranking_output_file}")
    print(f"Portfolio File: {portfolio_output_file}")
    print(f"Actions File  : {actions_file}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
