from config.config_loader import ConfigLoader
from repositories.parquet_repository import (
    ParquetRepository,
)
from services.report_service import ReportService


class AppContext:

    def __init__(self):

        #
        # Configuration
        #
        self.config = ConfigLoader.load()

        #
        # Repositories
        #
        self.price_repository = ParquetRepository(
            root="data/prices"
        )

        self.index_repository = ParquetRepository(
            root="data/indices"
        )
        
        self.report_service = ReportService()