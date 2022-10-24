#!python3
# -*- coding: utf-8 -*-
import argparse
import dataclasses
import json
import os
import subprocess

import boto3


class Actions:
    SHOW_TOAST = "show-toast"
    COPY = "copy"
    ADD_PARAM = "add-param"
    OPEN_URL = "open-url"


@dataclasses.dataclass
class Config:
    aws_profile: str
    region: str
    aws_vault: bool


def load_config():
    config_path = os.path.join(
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CONFIG_HOME")
        or os.path.join(os.environ["HOME"], ".config"),
        "aws_slapdash",
    )
    with open(os.path.join(config_path, "config.json")) as json_file:
        config_source = json.load(json_file)
        config = Config(
            aws_profile=config_source["profile"],
            region=config_source["region"],
            aws_vault=config_source["awsVault"],
        )
        return config


config = load_config()


def create_session(config: Config):
    envvars = subprocess.check_output(
        ["aws-vault", "exec", config.aws_profile, "--", "env"]
    )
    for envline in envvars.split(b"\n"):
        line = envline.decode("utf8")
        eqpos = line.find("=")
        if eqpos < 4:
            continue
        k = line[0:eqpos]
        v = line[eqpos + 1 :]
        if k == "AWS_ACCESS_KEY_ID":
            aws_access_key_id = v
        if k == "AWS_SECRET_ACCESS_KEY":
            aws_secret_access_key = v
        if k == "AWS_SESSION_TOKEN":
            aws_session_token = v

    return boto3.Session(
        aws_access_key_id,
        aws_secret_access_key,
        aws_session_token,
        config.region,
    )


session = create_session(config)


BASE_PATH = f"https://{config.region}.console.aws.amazon.com/"
DYNAMO_DB_DETAILS_URL = (
    BASE_PATH
    + f"dynamodbv2/home?region={config.region}#"
    + "table?name={table_name}"
)
TITLE_FORMAT = "{table_name}"

client = session.client("dynamodb")


def list_dd_tables():
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
                    "url": DYNAMO_DB_DETAILS_URL.format(table_name=table_name),
                },
                "moveAction": {
                    "type": "add-param",
                    "name": "table-name",
                    "value": table_name,
                },
            }
        )
    return resp


def serve_dynamodb_command(table_name):
    if not table_name:
        return list_dd_tables()
    table = client.describe_table(TableName=table_name)["Table"]
    item_count = table["ItemCount"]
    table_size = table["TableSizeBytes"]
    return [
        {
            "title": "Query Items",
            "action": {
                "type": Actions.OPEN_URL,
                "url": BASE_PATH
                + "dynamodbv2/home?table&table&region=eu-west-1#"
                + "item-explorer?initialTagKey=&maximize=true"
                + f"&table={table_name}",
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


def serve_command(get_response_func):
    parser = argparse.ArgumentParser(description="Manage Ec2 instances")
    parser.add_argument(
        "--table-name",
        help="Id of instance to manage",
    )
    args = parser.parse_args()
    resource_id = args.table_name
    print(
        json.dumps(
            {
                "view": {
                    "type": "list",
                    "options": get_response_func(resource_id),
                }
            }
        )
    )


serve_command(serve_dynamodb_command)
