import json
from argparse import ArgumentParser
from typing import Optional

from utils.slapdash import Actions

from aws_slapdash.utils.aws import Config, create_session
from aws_slapdash.utils.command import AWSServiceCommand


class Ec2Command(AWSServiceCommand):
    def __init__(self, config: Config):
        self.config = config

    def service_name(self):
        return "EC2"

    def serve_command(self, arg_parser: ArgumentParser):
        arg_parser.add_argument(
            "--instance-id",
            help="Id of instance to manage",
        )
        args = arg_parser.parse_args()

        print(
            json.dumps(
                {
                    "view": {
                        "type": "list",
                        "options": self.get_ec2_optoins(args.instance_id),
                    }
                }
            )
        )

    def service_url(self):
        return f"{self.aws_console_base_url}ec2/home"

    @property
    def aws_console_base_url(self) -> str:
        return f"https://{self.config.region}.console.aws.amazon.com/"

    def get_ec2_optoins(self, instance_id: Optional[str] = None):
        session = create_session()
        client = session.client("ec2")
        resource = session.resource("ec2")
        if not instance_id:
            return self.list_ec2_instances(client)
        instance = resource.Instance(instance_id)
        EC2_SSM_CONNECT = (
            f"{self.aws_console_base_url}systems-manager/session-manager/"
            "{instance_id}"
            f"?region={self.config.region}#"
        )
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

    def list_ec2_instances(self, client):
        ec2_instances = client.describe_instances()
        instances = []
        for reservation in ec2_instances["Reservations"]:
            instances.extend(reservation["Instances"])
        TITLE_FORMAT = "{instance_name} | {instance_id} | {instance_state} "
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
                        instance_name=name,
                        instance_id=id,
                        instance_state=state,
                    ),
                    "action": {
                        "type": Actions.OPEN_URL,
                        "url": (
                            f"{self.service_url}?region=eu-west-1"
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
