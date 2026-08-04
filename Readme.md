
# Momentum Investing Framework

## Overview

This project implements a quantitative momentum investing framework with a strong emphasis on:

- Configuration-driven design
- Shared architecture between Backtest and Live Portfolio generation
- Modular indicators
- Extensible scoring model
- Deterministic portfolio construction
- Research-friendly reporting

The framework is designed so that strategy changes are made through configuration whenever possible instead of modifying application code.

---

# Technology Stack

- Python 3.14.x
- pandas
- pyarrow
- PyYAML
- Virtual Environment (venv)

> Always use the same Python major/minor version used by the project. Mixing versions can produce different dependency behavior.

---

# Project Architecture

```
Universe
    │
    ▼
RankingService
    │
    ▼
PortfolioManager
    │
    ├── Backtest
    │       ▼
    │   Performance
    │       ▼
    │   Reports
    │
    └── Live
            ▼
        Current Portfolio
```

Backtest and Live intentionally share the same ranking and portfolio construction logic.

---

# Python Installation

## Verify Python

```bash
python3 --version
```

Expected:

```text
Python 3.14.x
```

If another version is returned, install Python 3.14 and recreate the virtual environment.

---

# Create Virtual Environment

```bash
python3.14 -m venv .venv
```

Activate

macOS/Linux

```bash
source .venv/bin/activate
```

Windows

```cmd
.venv\Scripts\activate
```

---

# Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

# Project Configuration

All strategy behaviour is controlled through:

```
config/strategy.yaml
```

Examples:

- Portfolio Size
- Rebalance Day
- Momentum Windows
- Factor Weights
- Market Filter
- Charges
- Universe

Whenever possible, prefer configuration changes over code changes.

---

# Update Market Data

Refresh all stock and index price data before running a backtest or generating the current portfolio.

Run:

```bash
python app.py
```

This application:

- Downloads the latest stock prices.
- Downloads the latest index prices.
- Updates the local parquet repository.
- Preserves historical data while appending new records.

Always run this step before executing a backtest or generating the current portfolio to ensure the framework uses the latest available market data.

---

# Run Backtest

```bash
python run_backtest.py
```

Generated reports are written to the reports/output directory.

Typical outputs include:

- Portfolio history
- Rankings
- Trades
- Performance summary
- Metrics

---

# Run Current Portfolio (Live)

```bash
python run_current_portfolio.py
```

This generates:

- Current Rankings
- Current Portfolio

No historical performance calculations are performed.

---

# Core Components

## RankingService

Responsible for:

- Loading market data
- Executing indicators
- Calculating scores
- Producing ranked stocks

## PortfolioManager

Responsible for:

- Building portfolios
- Rebalancing
- Buy/Sell decisions
- Trade creation

## PerformanceService

Calculates portfolio performance during backtests.

## ReportBuilder

Converts framework models into report models.

## CsvReportWriter

Writes report models to CSV.

CSV columns are generated automatically from report dataclasses.

---

# Design Principles

1. Backtest and Live must remain synchronized.
2. Business logic belongs in services.
3. Indicators perform calculations only.
4. Reports never contain business logic.
5. Prefer configuration over hardcoding.
6. Keep models simple data containers.

---

# Development Guidelines

When adding a new feature:

1. Add the model if required.
2. Add/update service logic.
3. Update report model.
4. Update report builder.
5. Verify both Backtest and Live remain aligned.

Never implement a framework feature in only one execution path.

---

# Future Enhancements

Planned enhancements include:

- Candidate Validator
- Liquidity filters
- Circuit filters
- Delisting handling
- Sector constraints
- Broker integration
- Additional momentum and quality factors

---

# Troubleshooting

## Module Not Found

Verify the virtual environment is activated.

## Incorrect Python Version

Run:

```bash
python --version
```

## Missing Price Data

Verify the required parquet files exist under the configured price repository directory.

## Backtest Results Changed Unexpectedly

Check:

- strategy.yaml
- Universe configuration
- Market filter configuration
- Price data refresh date
- Transaction cost settings

---

# Notes for Future Maintenance

The framework is intentionally modular.

Before modifying existing services:

- Preserve the shared Backtest/Live architecture.
- Avoid duplicating business logic.
- Prefer extending existing services instead of creating parallel implementations.
- Keep reports as projections of existing models rather than recalculating values.

Following these principles should allow the framework to remain understandable and maintainable even many years from now.