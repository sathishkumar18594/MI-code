import pandas as pd

from application.app_context import AppContext


class SignalCalendarService:

    def __init__(
        self,
        context: AppContext,
    ):

        self.context = context

        self.rebalance_day = (
            context.config["strategy"]["rebalance_day"]
        )

        self.repository = (
            context.index_repository
        )

        market_filter = context.config[
            "universe"
        ][
            "market_filter"
        ]

        self.index_name = (
            market_filter[
                "index"
            ][
                "name"
            ]
        )

        self.index_symbol = (
            market_filter[
                "index"
            ][
                "symbol"
            ]
        )

    def signal_dates(
        self,
        start_date,
        end_date,
    ):

        calendar = self.repository.load(
            self.index_name
        )

        calendar = calendar[
            (calendar["Date"] >= start_date)
            &
            (calendar["Date"] <= end_date)
        ].copy()

        signal_dates = []

        start = pd.Timestamp(start_date)

        end = pd.Timestamp(end_date)

        year = start.year
        month = start.month

        while (
            year < end.year
            or (
                year == end.year
                and month <= end.month
            )
        ):

            #
            # Calendar rebalance date
            #
            try:

                rebalance_date = pd.Timestamp(
                    year=year,
                    month=month,
                    day=self.rebalance_day,
                )

            except ValueError:

                #
                # Invalid calendar day
                # (example: Feb 30)
                #
                if month == 12:
                    year += 1
                    month = 1
                else:
                    month += 1

                continue

            #
            # First trading day on or after
            # the rebalance date
            #
            trading_days = calendar[
                calendar["Date"] >= rebalance_date
            ]

            if not trading_days.empty:

                signal_dates.append(
                    trading_days.iloc[0]["Date"]
                )

            #
            # Next month
            #
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

        return signal_dates