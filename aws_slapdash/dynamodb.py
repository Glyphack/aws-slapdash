import argparse
import json

from utils.aws import create_session
from utils.command import AWSServiceCommand
from utils.slapdash import Actions


class DynamoDBCommand(AWSServiceCommand):
    def service_name(self):
        return "DynamoDB"

    def service_url(self):
        return (
            self.aws_console_base_url
            + f"dynamodbv2/home?region={self.config.region}#"
        )

    def serve_command(self, arg_parser: argparse.ArgumentParser):
        arg_parser.add_argument(
            "--table-name",
            help="Id of instance to manage",
        )
        args = arg_parser.parse_args()
        resource_id = args.table_name
        print(
            json.dumps(
                {
                    "view": {
                        "type": "list",
                        "options": self.serve_dynamodb_command(resource_id),
                    }
                }
            )
        )

    def list_dd_tables(self, client):
        DYNAMO_DB_DETAILS_URL = (
            self.aws_console_base_url
            + f"dynamodbv2/home?region={self.config.region}#"
            + "table?name={table_name}"
        )
        TITLE_FORMAT = "{table_name}"
        list_tables_resp = client.list_tables()
        tables = list_tables_resp["TableNames"]
        while list_tables_resp.get("LastEvaluatedTableName") is not None:
            tables.extend(list_tables_resp["TableNames"])
            list_tables_resp = client.list_tables()
        resp = []
        for table in tables:
            table_name = table
            resp.append(
                {
                    "title": TITLE_FORMAT.format(
                        table_name=table_name,
                    ),
                    "action": {
                        "type": "open-url",
                        "url": DYNAMO_DB_DETAILS_URL.format(
                            table_name=table_name
                        ),
                    },
                    "moveAction": {
                        "type": "add-param",
                        "name": "table-name",
                        "value": table_name,
                    },
                }
            )
        return resp

    def serve_dynamodb_command(self, table_name):
        session = create_session()
        client = session.client("dynamodb")
        if not table_name:
            return self.list_dd_tables(client)
        table = client.describe_table(TableName=table_name)["Table"]
        item_count = table["ItemCount"]
        table_size = table["TableSizeBytes"]
        return [
            {
                "title": "Query Items",
                "action": {
                    "type": Actions.OPEN_URL,
                    "url": (
                        self.aws_console_base_url
                        + "dynamodbv2/home?table&table&region=eu-west-1#"
                        + "item-explorer?initialTagKey=&maximize=true"
                        + f"&table={table_name}"
                    ),
                },
            },
            {
                "title": f"Item count: {item_count}",
                "action": {"type": Actions.COPY, "value": str(item_count)},
            },
            {
                "title": f"Table Size: {table_size}",
                "action": {"type": Actions.COPY, "value": str(table_size)},
            },
        ]
