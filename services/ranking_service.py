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

    def rank(
        self,
        symbols: list[str],
        rebalance_date: datetime,
    ) -> list[Ranking]:

        rows = []

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
                df["Date"] <= rebalance_date
            ]

            if df.empty:
                print(
                    f"[NO DATA] {symbol} before {rebalance_date.date()}"
                )
                continue

            latest = df.iloc[-1].copy()

            latest["symbol"] = symbol

            rows.append(latest)

        print(f"[RANKING] Rows collected: {len(rows)}")
        if not rows:
            return []

        universe = pd.DataFrame(rows)

        universe = (
            self.scoring_service.calculate(
                universe
            )
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