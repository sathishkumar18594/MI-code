from datetime import datetime

from bootstrap import Bootstrap
from services.universe_service import UniverseService


bootstrap = Bootstrap()

calendar = bootstrap.signal_calendar_service()

backtest = bootstrap.backtest_service()

universe = UniverseService()

universe_name = bootstrap.context.config[
    "universe"
]["name"]

symbols = universe.get_universe(
    universe_name.lower()
)

signal_dates = calendar.signal_dates(
    start_date=datetime(2015, 1, 1),
    end_date=datetime.today(),
)

result = backtest.run(
    symbols=symbols,
    rebalance_dates=signal_dates,
)

print()
print("=" * 60)
print(f"Periods Created : {len(result.periods)}")
print("=" * 60)
print()

if result.periods:
    print("First 5 period returns:")
    for period in result.periods[:5]:
        print(period.performance.period_return)
    print()

print(result.metrics)

print()
print("=" * 60)
print("CSV reports generated successfully")
print("Location : reports/output")
print("=" * 60)
print()