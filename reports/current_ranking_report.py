

from models.current_portfolio_report import (
    CurrentPortfolioReport,
)


class CurrentRankingReport:

    def __init__(
        self,
        report: CurrentPortfolioReport,
    ):

        self.report = report

    @property
    def trading_date(self):
        return self.report.trading_date

    @property
    def portfolio(self):
        return self.report.portfolio

    @property
    def rankings(self):
        return self.report.rankings

    @property
    def rank_lookup(self):
        return self.report.rank_lookup