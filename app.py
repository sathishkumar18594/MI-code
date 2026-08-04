from providers.yahoo_provider import YahooProvider
from repositories.parquet_repository import ParquetRepository
from services.marketdata_service import MarketDataService
from services.universe_service import UniverseService
from services.validation_service import ValidationService
from pipelines.data_pipeline import DataPipeline
from services.index_service import IndexService

provider = YahooProvider()

# Stock repository
price_repository = ParquetRepository(
    root="data/prices"
)

# Index repository
index_repository = ParquetRepository(
    root="data/indices"
)

validator = ValidationService()

market_data = MarketDataService(
    provider=provider,
    repository=price_repository,
    validator=validator
)

index_service = IndexService(
    provider=provider,
    repository=index_repository,
    validator=validator
)

universe_service = UniverseService()

pipeline = DataPipeline(
    universe_service=universe_service,
    market_data_service=market_data,
    index_service=index_service
)

# ==========================================================
# Select Universe
# ==========================================================

UNIVERSE = "nifty500"
# UNIVERSE = "midcap250"

pipeline.run(UNIVERSE)