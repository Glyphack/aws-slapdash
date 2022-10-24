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
STACK_DETAILS_URL = (
    BASE_PATH
    + f"cloudformation/home?region={config.region}#/stacks/"
    + "stackinfo?filteringStatus=active&filteringText=&viewNested=true"
    + "&hideStacks=false&stackId={stack_id}"
)
TITLE_FORMAT = "{stack_name} | {stack_status}"

client = session.client("cloudformation")


def list_stacks():
    list_stacks_resp = client.list_stacks()
    stacks = list_stacks_resp["StackSummaries"]
    while list_stacks_resp.get("NextToken") is not None:
        list_stacks_resp = client.list_stacks(
            NextToken=list_stacks_resp["NextToken"]
        )
        stacks.extend(list_stacks_resp["StackSummaries"])
    active_stacks = filter(
        lambda s: s.get("DeletionTime") is None,
        stacks,
    )
    resp = []
    for stack in active_stacks:
        stack_name = stack["StackName"]
        stack_status = stack["StackStatus"]
        stack_id = stack["StackId"]
        resp.append(
            {
                "title": TITLE_FORMAT.format(
                    stack_name=stack_name, stack_status=stack_status
                ),
                "action": {
                    "type": "open-url",
                    "url": STACK_DETAILS_URL.format(stack_id=stack_id),
                },
            }
        )
    return resp


def serve_cloudformation_command(stack_name):
    if not stack_name:
        return list_stacks()


def serve_command(get_response_func):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stack-id",
    )
    _ = parser.parse_args()
    print(
        json.dumps(
            {
                "view": {
                    "type": "list",
                    "options": get_response_func(None),
                }
            }
        )
    )


serve_command(serve_cloudformation_command)
