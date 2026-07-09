from application.app_context import AppContext

from models.trade import Trade
from models.sell_reason import SellReason

from models.portfolio import Portfolio
from models.portfolio_state import PortfolioState
from models.portfolio_position import (
    PortfolioPosition,
)
from services.portfolio_accounting_service import (
    PortfolioAccountingService,
)

from services.execution_price_service import ExecutionPriceService
from services.transaction_cost_service import TransactionCostService


class PortfolioManager:

    def __init__(
        self,
        context: AppContext,
    ):

        self.context = context

        strategy = context.config["strategy"]

        self.portfolio_size = (
            strategy["portfolio_size"]
        )

        self.sell_rank_percent = (
            strategy.get(
                "sell_rank_percent",
                strategy.get(
                    "sell_threshold_percent",
                    10,
                ),
            )
        )

        portfolio = context.config["portfolio"]

        self.initial_capital = (
            portfolio["initial_capital"]
        )

        self.execution = ExecutionPriceService(context)
        self.transaction_cost = (
            TransactionCostService(context)
        )
        self.accounting = (
            PortfolioAccountingService()
        )

    def update(
        self,
        state: PortfolioState,
        rankings,
        market_bullish: bool,
        rebalance_date,
    ) -> PortfolioState:

        # Ensure initial capital is set only for the first investment
        if state.portfolio is None:
            state.cash = self.initial_capital

        #
        # Market turns bearish
        #
        if not market_bullish:
            if state.portfolio is not None:
                state.portfolio = self._liquidate_portfolio(
                    state.portfolio,
                    rebalance_date,
                )
            return PortfolioState(
                portfolio=state.portfolio,
                invested=False,
                cash=(
                    state.portfolio.cash
                    if state.portfolio is not None
                    else 1.0
                ),
            )

        #
        # First investment
        #
        if not state.invested:
            portfolio = self.build_new_portfolio(
                rankings,
                rebalance_date,
                capital=state.cash,
            )
            return PortfolioState(
                portfolio=portfolio,
                invested=True,
                cash=0.0,
            )

        #
        # Existing portfolio
        #
        portfolio = self.rebalance_existing_portfolio(
            state.portfolio,
            rankings,
            rebalance_date,
        )
        return PortfolioState(
            portfolio=portfolio,
            invested=True,
            cash=0.0,
        )

    def _mark_to_market(self, position, rebalance_date):
        execution = self.execution.execution_price(
            position.symbol,
            rebalance_date,
        )

        position.current_price = execution.price
        position.market_value = (
            position.quantity * position.current_price
        )
        position.unrealized_pnl = (
            position.market_value - position.cost_value
        )

    def _keep_holding(self, position, ranking, kept_holdings, held_symbols):
        position.rank = ranking.rank
        position.score = ranking.stock.score
        position.weight = 0.0

        kept_holdings.append(position)
        held_symbols.add(position.symbol)

    def _sell_holding(
        self,
        portfolio,
        position,
        rebalance_date,
        reason=SellReason.RANK_EXIT,
        exit_rank=None,
    ):

        realized = (
            position.market_value
            - position.cost_value
        )

        trade_charges = (
            self.transaction_cost.calculate_sell(
                position.market_value
            )
        )

        net_realized = (
            realized
            - trade_charges.total
        )

        # Trade history is the source of truth for realized P&L.

        portfolio.trades.append(
            Trade(
                symbol=position.symbol,
                entry_date=position.entry_date,
                entry_rank=position.entry_rank,
                exit_date=rebalance_date,
                exit_rank=exit_rank,
                entry_price=position.entry_price,
                exit_price=position.current_price,
                quantity=position.quantity,
                cost_value=position.cost_value,
                proceeds=position.market_value,
                gross_realized_pnl=realized,
                return_pct=(
                    realized / position.cost_value
                    if position.cost_value > 0
                    else 0.0
                ),
                brokerage=trade_charges.brokerage,
                stt=trade_charges.stt,
                exchange_charge=trade_charges.exchange_charge,
                sebi_charge=trade_charges.sebi_charge,
                gst=trade_charges.gst,
                stamp_duty=trade_charges.stamp_duty,
                total_charges=trade_charges.total,
                net_realized_pnl=net_realized,
                holding_days=(
                    rebalance_date
                    - position.entry_date
                ).days,
                sell_reason=reason,
            )
        )

        return (
            position.market_value
            - trade_charges.total
        )

    def _buy_replacement(
        self,
        ranking,
        allocation,
        rebalance_date,
    ):
        execution = self.execution.execution_price(
            ranking.stock.symbol,
            rebalance_date,
        )

        buy_charges = (
            self.transaction_cost.calculate_buy(
                allocation
            )
        )

        investable_amount = max(
            0.0,
            allocation - buy_charges.total
        )

        quantity = (
            investable_amount / execution.price
            if execution.price > 0
            else 0.0
        )

        return PortfolioPosition(
            symbol=ranking.stock.symbol,
            entry_date=execution.date,
            entry_rank=ranking.rank,
            entry_price=execution.price,
            quantity=quantity,
            current_price=execution.price,
            weight=0.0,
            rank=ranking.rank,
            score=ranking.stock.score,
            cost_value=allocation,
            market_value=investable_amount,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )

    def _update_weights(self, holdings):
        if not holdings:
            return

        total_value = sum(
            h.market_value
            for h in holdings
        )

        if total_value <= 0:
            return

        for holding in holdings:
            holding.weight = (
                holding.market_value
                / total_value
            )

    def _build_portfolio(
        self,
        previous_portfolio,
        rebalance_date,
        holdings,
        available_cash,
        period_realized_pnl=0.0,
    ):
        portfolio = Portfolio(
            rebalance_date=rebalance_date,
            holdings=holdings,
            initial_capital=previous_portfolio.initial_capital,
            cash=available_cash,
            available_cash=available_cash,
            realized_pnl=previous_portfolio.realized_pnl,
            # period_realized_pnl is not a Portfolio constructor arg anymore
            is_invested=bool(holdings),
            trades=previous_portfolio.trades,
        )
        portfolio = self.accounting.rebuild(
            portfolio,
            self.portfolio_size,
        )
        # Preserve the realized P&L generated by this rebalance.
        portfolio.period_realized_pnl = period_realized_pnl
        return portfolio
        

    
    def _liquidate_portfolio(
        self,
        portfolio,
        rebalance_date,
    ):
        available_cash = portfolio.cash
        period_realized_pnl = 0.0
        for holding in portfolio.holdings:
            self._mark_to_market(
                holding,
                rebalance_date,
            )
            period_realized_pnl += (
                holding.market_value
                - holding.cost_value
                - self.transaction_cost.calculate_sell(
                    holding.market_value
                ).total
            )
            available_cash += self._sell_holding(
                portfolio,
                holding,
                rebalance_date,
                SellReason.MARKET_EXIT,
            )
        portfolio.holdings.clear()

        return self._build_portfolio(
            portfolio,
            rebalance_date,
            [],
            available_cash,
            period_realized_pnl,
        )

    def build_new_portfolio(
        self,
        rankings,
        rebalance_date,
        capital,
    ):
        selected = rankings[: self.portfolio_size]
        if not selected:
            return Portfolio(
                rebalance_date=rebalance_date,
                holdings=[],
                is_invested=False,
            )
        weight = 1 / len(selected)
        allocation = (
            capital
            / len(selected)
        )
        holdings = []
        for ranking in selected:
            execution = self.execution.execution_price(
                ranking.stock.symbol,
                rebalance_date,
            )
            buy_charges = (
                self.transaction_cost.calculate_buy(
                    allocation
                )
            )
            investable_amount = max(
                0.0,
                allocation - buy_charges.total
            )
            quantity = (
                investable_amount
                / execution.price
                if execution.price > 0
                else 0.0
            )
            holdings.append(
                PortfolioPosition(
                    symbol=ranking.stock.symbol,
                    entry_date=execution.date,
                    entry_rank=ranking.rank,
                    entry_price=execution.price,
                    quantity=quantity,
                    current_price=execution.price,
                    weight=weight,
                    rank=ranking.rank,
                    score=ranking.stock.score,
                    cost_value=allocation,
                    market_value=investable_amount,
                    realized_pnl=0.0,
                    unrealized_pnl=0.0,
                )
            )
        self._update_weights(holdings)
        portfolio = Portfolio(
            rebalance_date=rebalance_date,
            holdings=[],
            initial_capital=capital,
            cash=0.0,
            available_cash=0.0,
            is_invested=False,
            trades=[],
        )

        return self._build_portfolio(
            portfolio,
            rebalance_date,
            holdings,
            0.0,
        )

    def rebalance_existing_portfolio(
        self,
        portfolio,
        rankings,
        rebalance_date,
    ):
        rank_lookup = {
            ranking.stock.symbol: ranking
            for ranking in rankings
        }
        universe_size = len(rankings)
        sell_rank = max(
            1,
            int(
                universe_size
                * self.sell_rank_percent
                / 100
            ),
        )
        available_cash = portfolio.cash
        opening_cash = available_cash
        total_sell_proceeds = 0.0
        total_buy_allocation = 0.0
        period_realized_pnl = 0.0
        # period_unrealized_pnl = 0.0  # Removed
        kept_holdings = []
        held_symbols = set()
        debug_dates = {
            "2015-01-21",
            "2015-02-23",
            "2015-03-23",
        }
        for position in portfolio.holdings:
            self._mark_to_market(position, rebalance_date)
            current_unrealized = position.unrealized_pnl
            ranking = rank_lookup.get(position.symbol)
            if ranking is None or ranking.rank > sell_rank:
                period_realized_pnl += (
                    position.market_value
                    - position.cost_value
                    - self.transaction_cost.calculate_sell(
                        position.market_value
                    ).total
                )
                proceeds = self._sell_holding(
                    portfolio,
                    position,
                    rebalance_date,
                    SellReason.RANK_EXIT,
                    exit_rank=(ranking.rank if ranking is not None else None),
                )
                total_sell_proceeds += proceeds
                available_cash += proceeds
                continue
            self._keep_holding(
                position,
                ranking,
                kept_holdings,
                held_symbols,
            )
            # Do not update unrealized_pnl or period_unrealized_pnl here; handled elsewhere
            if str(rebalance_date.date()) in debug_dates:
                print(
                    f"KEEP {position.symbol} "
                    f"Cost={position.cost_value:,.2f} "
                    f"MV={position.market_value:,.2f} "
                    f"Rank={ranking.rank}"
                )
        replacement_count = max(
            0,
            self.portfolio_size - len(kept_holdings),
        )
        if replacement_count > 0:
            for ranking in rankings:
                if len(kept_holdings) >= self.portfolio_size:
                    break
                if ranking.stock.symbol in held_symbols:
                    continue
                remaining_slots = (
                    self.portfolio_size
                    - len(kept_holdings)
                )
                if remaining_slots <= 0:
                    break
                allocation = (
                    available_cash
                    / remaining_slots
                )
                # Insert missing buy logic
                position = self._buy_replacement(
                    ranking,
                    allocation,
                    rebalance_date,
                )
                if str(rebalance_date.date()) in debug_dates:
                    print(
                        f"BUY  {position.symbol} "
                        f"Allocation={allocation:,.2f} "
                        f"Cost={position.cost_value:,.2f} "
                        f"MV={position.market_value:,.2f}"
                    )
                kept_holdings.append(position)
                held_symbols.add(position.symbol)
                # New positions start at cost. Their initial unrealized
                # P&L should not contribute to this month's market return.
                total_buy_allocation += allocation
                available_cash -= allocation
        remaining_cash = available_cash
        # Removed redundant unrealized P&L update loop
        self._update_weights(
            kept_holdings
        )
        # Removed assignments to period_realized_pnl and period_unrealized_pnl on portfolio
        if str(rebalance_date.date()) not in debug_dates:
            return self._build_portfolio(
                portfolio,
                rebalance_date,
                kept_holdings,
                remaining_cash,
                period_realized_pnl,
            )
        print("\n========== PORTFOLIO AFTER REBALANCE ==========")
        print(f"Date : {rebalance_date}")
        print(f"Opening Cash : {opening_cash:,.2f}")
        print(f"Sell Proceeds: {total_sell_proceeds:,.2f}")
        print(f"Buy Allocation: {total_buy_allocation:,.2f}")
        for h in kept_holdings:
            print(
                f"{h.symbol:12}"
                f" Qty={h.quantity:.4f}"
                f" Cost={h.cost_value:,.2f}"
                f" MV={h.market_value:,.2f}"
                f" UPNL={h.unrealized_pnl:,.2f}"
            )
        print(f"Cash      : {remaining_cash:,.2f}")
        print(f"Invested  : {sum(h.market_value for h in kept_holdings):,.2f}")
        print(f"Total     : {remaining_cash + sum(h.market_value for h in kept_holdings):,.2f}")
        expected_cash = opening_cash + total_sell_proceeds - total_buy_allocation
        print(f"Expected Cash : {expected_cash:,.2f}")
        print(f"Actual Cash   : {remaining_cash:,.2f}")
        print(f"Available Cash      : {available_cash:,.2f}")
        print(f"Replacement Count   : {replacement_count}")
        print(f"Allocation          : {allocation if replacement_count > 0 else 0:,.2f}")
        print(f"Remaining Cash      : {remaining_cash:,.2f}")
        print("==============================================\n")
        # Removed assignments to period_realized_pnl and period_unrealized_pnl on portfolio
        return self._build_portfolio(
            portfolio,
            rebalance_date,
            kept_holdings,
            remaining_cash,
            period_realized_pnl,
        )