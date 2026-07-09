from application.app_context import AppContext
from services.market_filter_service import MarketFilterService
from services.ranking_service import RankingService
from services.portfolio_manager import PortfolioManager
from services.current_portfolio_report_builder import CurrentPortfolioReportBuilder
from reports.current_ranking_report_writer import CurrentRankingReportWriter
from services.current_ranking_report_builder import CurrentRankingReportBuilder
from reports.current_portfolio_report_writer import CurrentPortfolioReportWriter


def main():
    context = AppContext()

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

    from services.universe_service import UniverseService

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

    if not market_filter.is_bullish(
        latest_date
    ):
        print(
            f"Market is bearish on "
            f"{latest_date.date()}. "
            f"No portfolio generated."
        )
        return

    rankings = ranking_service.rank(
        symbols=symbols,
        rebalance_date=latest_date,
    )

    # Removed inline import of CurrentRankingReport
    ranking_report = ranking_report_builder.build(
        trading_date=latest_date,
        rankings=rankings,
    )

    ranking_output_file = ranking_report_writer.write(
        ranking_report
    )

    portfolio = (
        portfolio_manager.build_new_portfolio(
            rankings=rankings,
            rebalance_date=latest_date,
            capital=context.config["portfolio"]["initial_capital"],
        )
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