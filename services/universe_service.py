from pathlib import Path
import io
import time

import pandas as pd
import requests

from utils.logger import logger


class UniverseService:

    URLS = {
        "nifty500": "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv",
        "midcap250": "https://niftyindices.com/IndexConstituent/ind_niftymidcap250list.csv"
    }

    def __init__(self):

        self.folder = Path("data/universe")
        self.folder.mkdir(parents=True, exist_ok=True)

    def _download(self, url):

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7)"
            )
        }

        retries = 3

        for attempt in range(1, retries + 1):

            try:

                logger.info(f"Downloading {url}")

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=(10, 60)
                )

                response.raise_for_status()

                return pd.read_csv(
                    io.StringIO(response.text)
                )

            except Exception as ex:

                logger.warning(
                    f"Attempt {attempt}/{retries} failed: {ex}"
                )

                if attempt == retries:
                    raise

                time.sleep(5)

    def refresh(self, universe_name: str):

        if universe_name not in self.URLS:
            raise ValueError(f"Unsupported universe: {universe_name}")

        logger.info(f"Refreshing {universe_name}")

        df = self._download(
            self.URLS[universe_name]
        )

        file = self.folder / f"{universe_name}.csv"

        df.to_csv(
            file,
            index=False
        )

        logger.info(
            f"{universe_name}.csv saved with {len(df)} stocks."
        )

        return df

    def get_universe(self, universe_name: str):

        file = self.folder / f"{universe_name}.csv"

        if file.exists():

            logger.info(
                f"Loading {universe_name}.csv"
            )

            df = pd.read_csv(file)

            return df["Symbol"].tolist()

        logger.info(
            f"{universe_name}.csv not found. Downloading..."
        )

        df = self.refresh(universe_name)

        return df["Symbol"].tolist()