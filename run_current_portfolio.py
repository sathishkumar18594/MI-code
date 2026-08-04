from datetime import datetime
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

    trading_dates = [
        latest_date
    ]

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

    state = PortfolioState(
        cash=context.config[
            "portfolio"
        ]["initial_capital"],
    )

    rankings = ranking_service.get_rankings(
        latest_date
    )

    state = portfolio_manager.update(
        state=state,
        rankings=rankings,
        market_bullish=market_bullish,
        rebalance_date=latest_date,
        is_rebalance_day=True,
    )

    portfolio = state.portfolio

    ranking_report = ranking_report_builder.build(
        trading_date=latest_date,
        rankings=rankings,
    )

    ranking_output_file = ranking_report_writer.write(
        ranking_report
    )

    report = report_builder.build(
        trading_date=latest_date,
        portfolio=portfolio,
        rankings=rankings,
    )

    portfolio_output_file = (
        portfolio_report_writer.write(
            report
        )
    )

    print()
    print("=" * 60)
    print("Current Portfolio Generated Successfully")
    print(f"Trading Date : {latest_date.date()}")
    print(f"Rankings File : {ranking_output_file}")
    print(f"Portfolio File: {portfolio_output_file}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()