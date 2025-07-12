import os
import boto3
from botocore.exceptions import ClientError
from crawler.models.crawler_result import CrawlerResult
from crawler.database.db import DB


class DynamoDB(DB):
    def __init__(self):
        check_local = os.environ.get("IS_LOCAL")
        if check_local is not None and check_local.lower() in ("1", "true"):
            print("DynamoDB LOCAL")
            self._dynamodb = boto3.resource("dynamodb",
                                            region_name=os.environ.get("AWS_REGION"),
                                            endpoint_url=os.environ.get("DYNAMO_ENDPOINT"))
        else:
            self._dynamodb = boto3.resource("dynamodb")
        self._table = None

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self._dynamodb.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                print(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        else:
            self._table = table
        return exists

    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table that can be used to store movie data.
        The table uses the release year of the movie as the partition key and the
        title as the sort key.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            print("Creating table", table_name)
            self._table = self._dynamodb.create_table(
                TableName=table_name,
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
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        except AttributeError as err:
            print("Fudeu", err)
        else:
            return self._table

    def add_item(self, item: CrawlerResult) -> None:
        try:
            self._table.put_item(Item=item.model_dump_json())
        except ClientError as err:
            print("Couldn't add to table %s. %s", self._table, err)
            raise
