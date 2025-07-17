import asyncio
import os
from dynaconf import Dynaconf
from crawler.database.dynamo_db import DynamoDB
from crawler.engine.crawler_engine import CrawlerEngine


def handler(event, context):
    print("Processing event", event, "context", context)
    name = event.get('name', 'acrc')
    env = os.environ.get('ENVIRONMENT', 'dev')
    config_file = f"config/{env}/{name}.yaml"
    lambda_config = Dynaconf(
        envvar_prefix=False,
        merge_enabled=True,
        settings_files=[
            "common.yaml",
            config_file
        ]
    )
    db = DynamoDB(name=name, table_name=lambda_config.table_name)
    loop = asyncio.get_event_loop()
    engine = CrawlerEngine(lambda_config, db=db)
    loop.run_until_complete(engine.run())
    print('Finished')
    return 'ok'
