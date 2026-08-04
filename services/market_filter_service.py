import pandas as pd

from application.app_context import AppContext
from indicators.supertrend_indicator import (
    SupertrendIndicator,
)
from utils.timeframe_converter import (
    TimeframeConverter,
)


class MarketFilterService:

    def __init__(
        self,
        context: AppContext,
    ):

        self.context = context

        self.repository = (
            context.index_repository
        )

        self.market_filter = (
            context.config["universe"]["market_filter"]
        )

        self.index_name = (
            self.market_filter["index"]["name"]
        )

        self.index_symbol = (
            self.market_filter["index"]["symbol"]
        )

        self.timeframe = (
            self.market_filter["timeframe"]
        )

        #
        # Load index only once
        #
        df = self.repository.load(
            self.index_name
        )

        #
        # Convert timeframe only once
        #
        self.market_data = (
            TimeframeConverter.convert(
                df=df,
                timeframe=self.timeframe,
            )
        )

        #
        # Calculate Supertrend only once
        #
        supertrend = self.market_filter[
            "supertrend"
        ]

        self.market_data = (
            SupertrendIndicator().execute(
                self.market_data,
                period=supertrend["period"],
                multiplier=supertrend["multiplier"],
            )
        )

    def is_bullish(
        self,
        rebalance_date: pd.Timestamp,
    ) -> bool:

        completed = self.market_data[
            self.market_data["Date"] <= rebalance_date
        ]

        if completed.empty:

            return False

        return bool(
            completed.iloc[-1]["trend"] == 1
        )