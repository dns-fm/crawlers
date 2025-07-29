import asyncio
import argparse
from dynaconf import Dynaconf
from crawler.engine.crawler_engine import CrawlerEngine
from crawler.database.dynamo_db import DynamoDB


async def main(config: Dynaconf):
    db = DynamoDB(name=config.name, table_name=config.table_name)
    engine = CrawlerEngine(config, db=db)
    return await engine.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config-file", type=str, default="config/dev/common.yaml")
    parser.add_argument("--config-file", type=str, default="config/dev/acrc.yaml")
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

    items = asyncio.run(main(global_config))
