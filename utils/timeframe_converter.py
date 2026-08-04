import pandas as pd


class TimeframeConverter:

    _RESAMPLE_RULES = {
        "WEEKLY": "W-FRI",
        "MONTHLY": "ME",
    }

    @classmethod
    def convert(
        cls,
        df: pd.DataFrame,
        timeframe: str,
    ) -> pd.DataFrame:

        if timeframe not in cls._RESAMPLE_RULES:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        result = df.copy()

        result["Date"] = pd.to_datetime(result["Date"])

        result = result.sort_values("Date")

        result = result.set_index("Date")

        #
        # Preserve the first trading day of each week
        #
        result["WeekStart"] = result.index

        result = (
            result
            .resample(cls._RESAMPLE_RULES[timeframe])
            .agg(
                {
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum",
                    "WeekStart": "first",
                }
            )
            .dropna()
            .reset_index()
        )

        #
        # Match TradingView labels
        #
        result["Date"] = result["WeekStart"]

        result = result.drop(
            columns=["WeekStart"]
        )

        return result