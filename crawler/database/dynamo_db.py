import os
import boto3
import hashlib
from botocore.exceptions import ClientError
from crawler.models.crawler_result import CrawlerResult
from crawler.database.db import DB


class DynamoDB(DB):
    def __init__(self, name: str, table_name: str):
        """
        args:
        name: nome da imobiliaria
        table_name: nome da table
        """
        self._name: str = name
        self._table_name: str = table_name
        check_local = os.environ.get("IS_LOCAL")
        if check_local is not None and check_local.lower() in ("1", "true"):
            print("DynamoDB LOCAL")
            self._dynamodb = boto3.resource("dynamodb",
                                            region_name=os.environ.get("AWS_REGION"),
                                            endpoint_url=os.environ.get("DYNAMO_ENDPOINT"))
        else:
            self._dynamodb = boto3.resource("dynamodb")
        exists: bool = self.exists()
        if not exists:
            self.create_table()
        self._table = self._dynamodb.Table(self._table_name)

    def exists(self):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self._dynamodb.Table(self._table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                print(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    self._table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        else:
            self._table = table
        return exists

    def create_table(self):
        """
        Creates an Amazon DynamoDB table that can be used to store movie data.
        The table uses the release year of the movie as the partition key and the
        title as the sort key.

        :return: The newly created table.
        """
        try:
            print("Creating table", self._table_name)
            self._table = self._dynamodb.create_table(
                TableName=self._table_name,
                KeySchema=[
                    {"AttributeName": "name", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "url", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "name", "AttributeType": "S"},
                    {"AttributeName": "url", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
            self._table.wait_until_exists()
        except ClientError as err:
            print(
                "Couldn't create table %s. Here's why: %s: %s",
                self._table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        except AttributeError as err:
            print(err)
        else:
            return self._table

    def add_item(self, item: CrawlerResult) -> None:
        try:
            _item = item.model_dump()
            _item["markdown"] = hashlib.sha256(item.markdown.encode("utf-8")).hexdigest(),
            _item["created_at"] = item.created_at.isoformat()
            _item["updated_at"] = item.created_at.isoformat()
            self._table.put_item(Item=_item)
        except ClientError as err:
            print("Couldn't add to table %s. %s", self._table, err)
            raise

    def filter_existing(self, urls: list[str]) -> list[str]:
        keys = [{'PartitionKey': self._name,
                 'SortKey': url} for url in urls]
        try:
            response = self._dynamodb.batch_get_item(
                RequestItems={
                    self._table_name: {'Keys': keys, 'ProjectionExpression': 'PartitionKey'}
                }
            )
            items = response.get('Responses', {}).get(self._table_name, [])
            retrieved = set([item['PartitionKey'] for item in items])
            return list(set(urls).difference(retrieved))
        except Exception as ex:
            print("Error checking keys", ex)
        return urls
