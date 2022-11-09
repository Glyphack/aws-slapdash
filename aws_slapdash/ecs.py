import json
from argparse import ArgumentParser

from utils.slapdash import Actions

from aws_slapdash.utils.aws import Config, create_session
from aws_slapdash.utils.command import AWSServiceCommand


class EcsCommand(AWSServiceCommand):
    def __init__(self, config: Config):
        self.config = config

    def service_name(self):
        return "ECS"

    def serve_command(self, arg_parser: ArgumentParser):
        arg_parser.add_argument(
            "--cluster-name",
        )
        args = arg_parser.parse_args()
        print(
            json.dumps(
                {
                    "view": {
                        "type": "list",
                        "options": self.get_ecs_options(args.cluster_name),
                    }
                }
            )
        )

    def service_url(self):
        return f"{self.aws_console_base_url}ecs/v2/clusters/"

    def get_ecs_options(self, cluster_name: str):
        session = create_session()
        client = session.client("ecs")
        if not cluster_name:
            return self.list_clusters(client)
        CLUSTER_TASKS_URL = (
            self.cluster_url() + f"/task?region={self.config.region}"
        )
        CLUSTER_RUN_TASK_URL = (
            self.cluster_url() + f"/run-task?region={self.config.region}"
        )
        TASK_LOGS_URL = (
            self.cluster_url()
            + "/tasks/{short_name}/logs"
            + f"?region={self.config.region}"
        )
        resp = [
            {
                "title": "Run a new task",
                "action": {
                    "type": Actions.OPEN_URL,
                    "url": CLUSTER_RUN_TASK_URL.format(
                        cluster_name=cluster_name
                    ),
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
            task_definition_short_name = task["taskDefinitionArn"].split("/")[
                -1
            ]
            resp.append(
                {
                    "title": f"Task {task_definition_short_name} Logs",
                    "action": {
                        "type": Actions.OPEN_URL,
                        "url": TASK_LOGS_URL.format(
                            cluster_name=cluster_name, short_name=short_name
                        ),
                    },
                },
            )

        return resp

    def cluster_url(self):
        return self.aws_console_base_url + "ecs/v2/clusters/{cluster_name}"

    def list_clusters(self, client):
        CLUSTER_SERVICES_URL = (
            self.cluster_url() + f"/services?region={self.config.region}"
        )

        CLUSTER_TITLE_FORMAT = "{cluster_name} | {cluster_status}"
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
            cluster_name = cluster_detail["clusterName"]
            cluster_status = cluster_detail["status"]
            resp.append(
                {
                    "title": CLUSTER_TITLE_FORMAT.format(
                        cluster_name=cluster_name,
                        cluster_status=cluster_status,
                    ),
                    "action": {
                        "type": Actions.OPEN_URL,
                        "url": CLUSTER_SERVICES_URL.format(
                            cluster_name=cluster_name
                        ),
                    },
                    "moveAction": {
                        "type": Actions.ADD_PARAM,
                        "name": "cluster-name",
                        "value": cluster_name,
                    },
                }
            )
        return resp
