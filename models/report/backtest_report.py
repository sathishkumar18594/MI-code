from dataclasses import dataclass, field

from models.monthly_return_matrix import MonthlyReturnMatrix
from models.report.summary_report import (
    SummaryReport,
)
from models.report.monthly_report import (
    MonthlyReport,
)
from models.report.holding_report import (
    HoldingReport,
)
from models.report.trade_report import (
    TradeReport,
)
from models.report.annual_report import (
    AnnualReport,
)
from models.report.transaction_cost_report import (
    TransactionCostReport,
)
from models.report.metric_report import (
    MetricReport,
)
from models.report.decision_report import (
    DecisionReport,
)


@dataclass(slots=True)
class BacktestReport:

    summary: SummaryReport | None = None

    monthly: list[
        MonthlyReport
    ] = field(
        default_factory=list
    )

    holdings: list[
        HoldingReport
    ] = field(
        default_factory=list
    )

    trades: list[
        TradeReport
    ] = field(
        default_factory=list
    )

    annual: list[
        AnnualReport
    ] = field(
        default_factory=list
    )

    transaction_costs: list[
        TransactionCostReport
    ] = field(
        default_factory=list
    )

    metrics: MetricReport | None = None

    decisions: list[
        DecisionReport
    ] = field(
        default_factory=list
    )
    
    monthly_return_matrix: list[MonthlyReturnMatrix] = field(
        default_factory=list
    )