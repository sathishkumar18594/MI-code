from datetime import datetime

import pandas as pd

from application.app_context import AppContext
from indicators.indicator_pipeline import (
    IndicatorPipeline,
)
from mappers.stock_snapshot_mapper import (
    StockSnapshotMapper,
)
from models.ranking import Ranking
from services.scoring_service import (
    ScoringService,
)
from services.liquidity_service import (
    LiquidityService,
)


class RankingService:

    def __init__(
        self,
        context: AppContext,
    ):

        self.context = context

        self.repository = (
            context.price_repository
        )

        self.pipeline = (
            IndicatorPipeline(
                context
            )
        )

        self.scoring_service = (
            ScoringService(
                context
            )
        )
        self.liquidity_service = (
            LiquidityService(
                context
            )
        )

        self.cache = {}
        self.dataframes = {}
    def _build_dataframe_cache(
        self,
        symbols: list[str],
    ):
        self.dataframes.clear()
        for symbol in symbols:
            if not self.repository.exists(symbol):
                print(f"[MISSING] {symbol}")
                continue
            df = self.repository.load(symbol)
            print(
                f"[LOAD] {symbol} rows={len(df)} last_date={df['Date'].max()}"
            )
            df = self.pipeline.execute(df)
            self.dataframes[symbol] = df

    def _collect_rows(
        self,
        symbols: list[str],
        trading_date: datetime,
        use_dataframe_cache: bool,
    ):
        rows = []
        if use_dataframe_cache:
            for symbol in symbols:
                df = self.dataframes.get(symbol)
                if df is None:
                    continue
                # Binary search on the sorted Date column.
                idx = df["Date"].searchsorted(trading_date, side="right") - 1
                if idx < 0:
                    print(
                        f"[NO DATA] {symbol} before {trading_date.date()}"
                    )
                    continue
                history = df.iloc[:idx + 1]

                latest = history.iloc[-1].copy()
                latest["symbol"] = symbol
                latest["average_daily_traded_value"] = (
                    self.liquidity_service
                    .average_daily_traded_value(history)
                )
                rows.append(latest)
        else:
            for symbol in symbols:
                if not self.repository.exists(symbol):
                    print(f"[MISSING] {symbol}")
                    continue

                df = self.repository.load(symbol)
                print(
                    f"[LOAD] {symbol} rows={len(df)} last_date={df['Date'].max()}"
                )

                df = self.pipeline.execute(df)

                df = df[
                    df["Date"] <= trading_date
                ]

                if df.empty:
                    print(
                        f"[NO DATA] {symbol} before {trading_date.date()}"
                    )
                    continue

                latest = df.iloc[-1].copy()

                latest["symbol"] = symbol
                latest["average_daily_traded_value"] = (
                    self.liquidity_service
                    .average_daily_traded_value(df)
                )

                rows.append(latest)

        print(f"[RANKING] Rows collected: {len(rows)}")
        return rows

    def _build_rankings(
        self,
        rows,
    ) -> list[Ranking]:
        if not rows:
            return []

        universe = pd.DataFrame(rows)

        universe = (
            self.scoring_service.calculate(
                universe
            )
        )

        universe = self.liquidity_service.filter(
            universe
        )

        universe = (
            universe
            .sort_values(
                by="score",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        rankings = []

        for index, (_, row) in enumerate(
            universe.iterrows(),
            start=1,
        ):

            snapshot = (
                StockSnapshotMapper.from_series(
                    row
                )
            )

            factor_values = (
                self.scoring_service.get_factor_values(
                    row
                )
            )
            rankings.append(
                Ranking(
                    rank=index,
                    stock=snapshot,
                    score=row["score"],
                    factor_values=factor_values,
                )
            )

        return rankings

    def rank(
        self,
        symbols: list[str],
        rebalance_date: datetime,
    ) -> list[Ranking]:

        rows = self._collect_rows(
            symbols=symbols,
            trading_date=rebalance_date,
            use_dataframe_cache=False,
        )
        return self._build_rankings(rows)

    def build_cache(
        self,
        symbols: list[str],
        trading_dates: list[datetime],
    ):
        self.cache.clear()
        self._build_dataframe_cache(symbols)
        for trading_date in trading_dates:
            rows = self._collect_rows(
                symbols=symbols,
                trading_date=trading_date,
                use_dataframe_cache=True,
            )
            self.cache[trading_date] = self._build_rankings(rows)

    def get_rankings(
        self,
        trading_date: datetime,
    ) -> list[Ranking]:
        return self.cache.get(trading_date, [])
