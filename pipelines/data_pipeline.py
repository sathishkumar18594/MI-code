class DataPipeline:

    def __init__(
        self,
        universe_service,
        market_data_service,
        index_service
    ):

        self.universe_service = universe_service
        self.market_data_service = market_data_service
        self.index_service = index_service

    def run(
        self,
        universe_name
    ):

        self.index_service.update()

        universe = self.universe_service.get_universe(
            universe_name
        )

        self.market_data_service.update_all(
            universe
        )
        self.market_data_service.update_symbol("GOLDBEES")
