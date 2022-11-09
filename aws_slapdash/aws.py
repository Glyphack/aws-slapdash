#!python3
# -*- coding: utf-8 -*-

import argparse
import json
from typing import Dict, Type

from aws_slapdash import cloudformation, dynamodb, ec2, ecs, secretsmanager
from aws_slapdash.configure import load_config, serve_config_command
from aws_slapdash.utils.command import AWSServiceCommand


def server_aws_command():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--service-name",
    )
    parser.add_argument("--configure")
    args, _ = parser.parse_known_args()

    service_name_server_table: Dict[str, Type[AWSServiceCommand]] = {
        "cloudformation": cloudformation.CloudformationCommand,
        "dynamodb": dynamodb.DynamoDBCommand,
        "ec2": ec2.Ec2Command,
        "ecs": ecs.EcsCommand,
        "secretsmanager": secretsmanager.SecretsManagerCommand,
    }
    config = load_config()
    if args.service_name:
        command_server = service_name_server_table[args.service_name](config)
        command_server.serve_command(parser)
    elif args.configure:
        serve_config_command(parser)
    else:
        options = [
            {
                "title": "configure",
                "action": {"type": "open-url", "url": ""},
                "moveAction": {
                    "type": "add-param",
                    "name": "configure",
                    "value": "true",
                },
            },
        ]
        options.extend(
            [
                {
                    "title": service(config).service_name(),
                    "action": {
                        "type": "open-url",
                        "url": service(config).service_url(),
                    },
                    "moveAction": {
                        "type": "add-param",
                        "name": "service",
                        "value": command_name,
                    },
                }
                for command_name, service in service_name_server_table.items()
            ]
        )
        print(
            json.dumps(
                {
                    "view": {
                        "type": "list",
                        "options": options,
                    }
                }
            )
        )


if __name__ == "__main__":
    server_aws_command()
