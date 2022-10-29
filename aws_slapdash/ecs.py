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

BASE_PATH = f"https://{config.region}.console.aws.amazon.com"
CLUSTER_BASE_PATH = BASE_PATH + "/ecs/v2/clusters/{cluster_name}"
CLUSTER_SERVICES_URL = CLUSTER_BASE_PATH + f"/services?region={config.region}"
CLUSTER_TASKS_URL = CLUSTER_BASE_PATH + f"/task?region={config.region}"
CLUSTER_RUN_TASK_URL = CLUSTER_BASE_PATH + f"/run-task?region={config.region}"
TASK_LOGS_URL = (
    CLUSTER_BASE_PATH + "/tasks/{short_name}/logs" + f"?region={config.region}"
)
CLUSTER_TITLE_FORMAT = "{cluster_name} | {cluster_status}"

client = session.client("ecs")


def list_clusters():
    list_clusters_resp = client.list_clusters()
    clusters = list_clusters_resp["clusterArns"]
    while list_clusters_resp.get("nextToken") is not None:
        clusters.extend(list_clusters_resp["clusterArns"])
        list_clusters_resp = client.list_clusters()

    described_clusters = client.describe_clusters(
        clusters=clusters,
    )["clusters"]

    resp = []
    for cluster_detail in described_clusters:
        cluster_arn = cluster_detail["clusterArn"]
        cluster_name = cluster_detail["clusterName"]
        cluster_status = cluster_detail["status"]
        resp.append(
            {
                "title": CLUSTER_TITLE_FORMAT.format(
                    cluster_name=cluster_name,
                    cluster_status=cluster_status,
                ),
                "action": {
                    "type": "open-url",
                    "url": CLUSTER_SERVICES_URL.format(
                        cluster_name=cluster_name
                    ),
                },
                "moveAction": {
                    "type": "add-param",
                    "name": "cluster-name",
                    "value": cluster_name,
                },
            }
        )
    return resp


def command_entry_point(cluster_name: str):
    if not cluster_name:
        return list_clusters()

    resp = [
        {
            "title": "Run a new task",
            "action": {
                "type": "open-url",
                "url": CLUSTER_RUN_TASK_URL.format(cluster_name=cluster_name),
            },
        },
    ]
    list_tasks_resp = client.list_tasks(cluster=cluster_name)
    if not list_tasks_resp["taskArns"]:
        return resp
    describe_tasks_resp = client.describe_tasks(
        cluster=cluster_name, tasks=list_tasks_resp["taskArns"]
    )
    for task in describe_tasks_resp["tasks"]:
        task_arn = task["taskArn"]
        short_name = task_arn.split("/")[-1]
        task_definition_short_name = task["taskDefinitionArn"].split("/")[-1]
        resp.append(
            {
                "title": f"Task {task_definition_short_name} Logs",
                "action": {
                    "type": "open-url",
                    "url": TASK_LOGS_URL.format(
                        cluster_name=cluster_name, short_name=short_name
                    ),
                },
            },
        )

    return resp


def serve_command(get_response_func):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cluster-name",
    )
    args = parser.parse_args()
    cluster_name = args.cluster_name
    print(
        json.dumps(
            {
                "view": {
                    "type": "list",
                    "options": get_response_func(cluster_name),
                }
            }
        )
    )


serve_command(command_entry_point)
