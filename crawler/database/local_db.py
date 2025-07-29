import pandas as pd
from crawler.models.crawler_result import CrawlerResult
from crawler.database.db import DB


class LocalDB(DB):
    def __init__(self, output_file: str):
        print(f"Saving results to {output_file}")
        self._output_file = output_file

    def add_item(self, item: CrawlerResult):
        with open(self._output_file, 'a') as fp:
            json_line = item.model_dump_json()
            fp.write(json_line + '\n')

    def filter_existing(self, urls: list[str]) -> list[str]:
        df = pd.read_json(self._output_file, lines=True)
        if df.empty:
            return urls
        existing = set(df.url)
        return list(set(urls).difference(existing))
