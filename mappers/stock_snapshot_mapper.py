import pandas as pd

from models.stock_snapshot import StockSnapshot


class StockSnapshotMapper:

    @staticmethod
    def from_series(
        row: pd.Series,
    ) -> StockSnapshot:

        return StockSnapshot(

            symbol=row["symbol"],

            date=row["Date"].to_pydatetime(),

            close=float(row["Close"]),

            return_3m=float(row["return_3m"]),

            return_6m=float(row["return_6m"]),

            return_9m=float(row["return_9m"]),

            volatility_3m=float(
                row["volatility_3m"]
            ),

            score=float(
                row["score"]
            ),
        )