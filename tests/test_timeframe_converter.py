import pandas as pd

from utils.timeframe_converter import (
    TimeframeConverter,
)


def test_weekly_conversion():

    df = pd.read_parquet(
        "data/prices/RELIANCE.parquet"
    )

    weekly = TimeframeConverter.convert(
        df=df,
        timeframe="WEEKLY",
    )

    assert len(weekly) < len(df)

    assert {
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    }.issubset(
        weekly.columns
    )

    print()

    print("=" * 80)

    print("Last 10 Weekly Candles")

    print("=" * 80)

    print(
        weekly[
            [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]
        ].tail(10)
    )