#!python3
# -*- coding: utf-8 -*-
import argparse

# generated-begin
import dataclasses
import json
import os
import subprocess
import typing

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


def slapdash_show_message_and_exit(msg: str) -> None:
    """
    Useful for showing error messages
    """
    print(json.dumps({"view": msg}))
    exit()


def load_config() -> Config:
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


def create_session(config: Config) -> boto3.session.Session:
    envvars = subprocess.check_output(
        ["aws-vault", "exec", config.aws_profile, "--", "env"]
    )
    aws_access_key_id = None
    aws_secret_access_key = None
    aws_session_token = None
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
    if (
        aws_session_token is None
        or aws_secret_access_key is None
        or aws_access_key_id is None
    ):
        slapdash_show_message_and_exit(
            f"could not authenticate with aws-vault, response: {envvars}"
        )

    return boto3.Session(
        aws_access_key_id,
        aws_secret_access_key,
        aws_session_token,
        config.region,
    )


session = create_session(config)
# generated-end

client = session.client("secretsmanager")


BASE_PATH = f"https://{config.region}.console.aws.amazon.com"
SECRET_DETAILS_URL = BASE_PATH + "/secretsmanager/secret?name={secret_name}"
TITLE_FORMAT = "{secret_name}"


def get_items_response(secret_name: typing.Optional[str] = None):
    if not secret_name:
        return get_default_list_view()
    secret_value = client.get_secret_value(SecretId=secret_name)[
        "SecretString"
    ]
    return [
        {
            "title": "Copy secret name",
            "action": {
                "type": Actions.COPY,
                "value": secret_name,
            },
        },
        {
            "title": "Copy secret",
            "action": {
                "type": Actions.COPY,
                "value": secret_value,
            },
        },
    ]


def get_default_list_view():
    secrets = client.list_secrets()
    resp = []
    for secret in secrets["SecretList"]:
        name = secret["Name"]
        resp.append(
            {
                "title": TITLE_FORMAT.format(secret_name=name),
                "action": {
                    "type": "open-url",
                    "url": SECRET_DETAILS_URL.format(secret_name=name),
                },
                "moveAction": {
                    "type": "add-param",
                    "name": "secret-name",
                    "value": name,
                },
            }
        )
    return resp


parser = argparse.ArgumentParser(description="Manage Ec2 instances")
parser.add_argument(
    "--secret-name",
    help="Id of instance to manage",
)
args = parser.parse_args()
secret_name = args.secret_name

print(
    json.dumps(
        {
            "view": {
                "type": "list",
                "options": get_items_response(secret_name),
            }
        }
    )
)
