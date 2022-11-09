import dataclasses
import json
import os
import subprocess

import boto3
from utils.slapdash import slapdash_show_message_and_exit


@dataclasses.dataclass
class Config:
    aws_profile: str
    region: str
    aws_vault: bool


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


def create_session(config: Config = load_config()) -> boto3.session.Session:
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
