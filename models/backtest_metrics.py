from dataclasses import dataclass


@dataclass(slots=True)
class BacktestMetrics:

    total_return: float = 0.0

    annual_return: float = 0.0

    cagr: float = 0.0

    max_drawdown: float = 0.0

    sharpe_ratio: float = 0.0

    sortino_ratio: float = 0.0

    calmar_ratio: float = 0.0

    win_rate: float = 0.0