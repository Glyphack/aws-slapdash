#!python3
# -*- coding: utf-8 -*-

import argparse
import dataclasses
import json
import os
import pathlib
import sys

import boto3


@dataclasses.dataclass
class Config:
    aws_profile: str
    region: str
    aws_vault: bool


def get_config_path():
    return os.path.join(
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CONFIG_HOME")
        or os.path.join(os.environ["HOME"], ".config"),
        "aws_slapdash",
    )


def load_config() -> Config:
    config_path = get_config_path()
    with open(os.path.join(config_path, "config.json")) as json_file:
        config_source = json.load(json_file)
        config = Config(
            aws_profile=config_source["profile"],
            region=config_source["region"],
            aws_vault=config_source["awsVault"],
        )
        return config


def store_config(config: Config):
    config_path = get_config_path()
    pathlib.Path(config_path).mkdir(exist_ok=True)
    config_file = os.path.join(config_path, "config.json")
    with open(config_file, "w+") as json_file:
        config_json = {
            "profile": config.aws_profile,
            "region": config.region,
            "awsVault": config.aws_vault,
        }
        json_file.write(json.dumps(config_json))


def serve_config_command():
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--profile",
        )
        parser.add_argument(
            "--region",
        )
        parser.add_argument(
            "--use-aws-vault", action="store", default=False, type=bool
        )
        args = parser.parse_args()
        config = Config(args.profile, args.region, args.use_aws_vault)
        store_config(config)

    else:
        try:
            config = load_config()
        except FileNotFoundError:
            config = Config("", "", False)

    print(
        json.dumps(
            {
                "view": {
                    "type": "form",
                    "title": "AWS Config",
                    "submitLabel": "Save",
                    "fields": [
                        {
                            "type": "text",
                            "id": "profile",
                            "label": "AWS profile",
                            "defaultValue": config.aws_profile,
                        },
                        {
                            "type": "select",
                            "id": "region",
                            "label": "Region",
                            "options": [
                                "eu-west-1",
                                "eu-west-2",
                                "eu-west-3",
                                "eu-north-1",
                                "eu-central-1",
                                "us-east-1",
                                "us-east-2",
                                "us-west-1",
                                "us-west-2",
                                "ap-south-1",
                                "ap-northeast-1",
                                "ap-northeast-2",
                                "ap-northeast-3",
                                "ap-southeast-2",
                                "ca-central-1",
                                "sa-east-1",
                            ],
                            "defaultValue": config.region,
                        },
                        {
                            "type": "toggle",
                            "id": "use-aws-vault",
                            "label": "AWS vault",
                            "defaultValue": config.aws_vault,
                        },
                    ],
                }
            }
        )
    )


serve_config_command()
