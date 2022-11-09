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

client = session.client("ec2")
resource = session.resource("ec2")


BASE_PATH = f"https://{config.region}.console.aws.amazon.com"
EC2_SSM_CONNECT = (
    f"{BASE_PATH}/systems-manager/session-manager/"
    "{instance_id}"
    f"?region={config.region}#"
)
TITLE_FORMAT = "{instance_name} | {instance_id} | {instance_state} "


def get_items_response(instance_id: typing.Optional[str] = None):
    if not instance_id:
        return get_default_list_view()
    instance = resource.Instance(instance_id)
    # Could not find an easy way to get key type
    key_type = "pem"
    return [
        {
            "title": "Connect Via SSM",
            "action": {
                "type": Actions.OPEN_URL,
                "url": EC2_SSM_CONNECT.format(instance_id=instance_id),
            },
        },
        {
            "title": "Copy public DNS name",
            "action": {
                "type": Actions.COPY,
                "value": instance.public_dns_name,
            },
        },
        {
            "title": "Copy ssh command",
            "action": {
                "type": Actions.COPY,
                "value": (
                    f"ssh -i '{instance.key_name}.{key_type}' "
                    f"ec2-user@{instance.public_dns_name}"
                ),
            },
        },
    ]


def get_default_list_view():
    ec2_instances = client.describe_instances()
    instances = []
    for reservation in ec2_instances["Reservations"]:
        instances.extend(reservation["Instances"])
    resp = []
    for instance in instances:
        id = instance["InstanceId"]
        state = instance["State"]["Name"]
        name = "{no name}"
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
        resp.append(
            {
                "title": TITLE_FORMAT.format(
                    instance_name=name, instance_id=id, instance_state=state
                ),
                "action": {
                    "type": Actions.OPEN_URL,
                    "url": (
                        f"{BASE_PATH}/ec2/home?region=eu-west-1"
                        f"#InstanceDetails:instanceId={id}"
                    ),
                },
                "moveAction": {
                    "type": "add-param",
                    "name": "instance-id",
                    "value": id,
                },
            }
        )
    return resp


parser = argparse.ArgumentParser(description="Manage Ec2 instances")
parser.add_argument(
    "--instance-id",
    help="Id of instance to manage",
)
args = parser.parse_args()
instance_id = args.instance_id

print(
    json.dumps(
        {
            "view": {
                "type": "list",
                "options": get_items_response(instance_id),
            }
        }
    )
)
