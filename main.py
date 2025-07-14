import asyncio
import pandas as pd
import argparse
from dynaconf import Dynaconf
from crawler.engine.crawler_engine import CrawlerEngine
from crawler.database.db import DB
from crawler.models.crawler_result import CrawlerResult


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


async def main(config: Dynaconf, output_file: str):
    local_db = LocalDB(output_file)
    engine = CrawlerEngine(config, db=local_db)
    return await engine.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config-file", type=str, default="config/common.yaml")
    parser.add_argument("--config-file", type=str, default="config/acrc.yaml")
    parser.add_argument("--output-file", type=str, default="imoveis.json")
    params = parser.parse_args()

    print(f"Running crawler with {params.config_file}")
    global_config = Dynaconf(
        envvar_prefix="",
        merge_enabled=True,
        settings_files=[
           params.base_config_file,
           params.config_file
        ]
    )

    items = asyncio.run(main(global_config, params.output_file))
