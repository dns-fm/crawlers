import asyncio
import os
from dynaconf import Dynaconf
from crawler.database.db import DB
from crawler.engine.crawler_engine import CrawlerEngine


def handler(event, context):
    print("Processing event", event, "context", context)
    value = event.get('name')
    config_file = os.environ.get("CONFIG_FILE", "acrc.yaml")
    if value:
        config_file = f"{value}.yaml"
    lambda_config = Dynaconf(
        envvar_prefix=False,
        merge_enabled=True,
        settings_files=[
            "common.yaml",
            config_file
        ]
    )
    db = DB()
    exists: bool = db.exists(lambda_config.table_name)
    if not exists:
        db.create_table(lambda_config.table_name)

    loop = asyncio.get_event_loop()
    engine = CrawlerEngine(lambda_config, db=db)
    loop.run_until_complete(engine.run())
    print('Finished')
    return 'ok'
