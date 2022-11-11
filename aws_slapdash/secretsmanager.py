import json
from argparse import ArgumentParser
from typing import Optional

from utils.slapdash import Actions

from aws_slapdash.utils.aws import create_session
from aws_slapdash.utils.command import AWSServiceCommand


class SecretsManagerCommand(AWSServiceCommand):
    def service_name(self):
        return "Secrets Manager"

    def service_url(self):
        return f"{self.aws_console_base_url}/secretsmanager/secret"

    def serve_command(self, arg_parser: ArgumentParser):
        arg_parser.add_argument(
            "--secret-name",
        )
        args = arg_parser.parse_args()

        print(
            json.dumps(
                {
                    "view": {
                        "type": "list",
                        "options": self.serve_secrets_manager_command(
                            args.secret_name
                        ),
                    }
                }
            )
        )

    def serve_secrets_manager_command(self, secret_name: Optional[str] = None):
        session = create_session()
        client = session.client("secretsmanager")
        if not secret_name:
            return self.get_list_secrets_view(client)
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

    def get_list_secrets_view(self, client):
        list_secrets_resp = client.list_secrets()
        secrets = list_secrets_resp["SecretList"]
        while list_secrets_resp.get("NextToken"):
            list_secrets_resp = client.list_secrets(
                NextToken=list_secrets_resp["NextToken"]
            )
            secrets.extend(list_secrets_resp["SecretList"])
        resp = []

        SECRET_DETAILS_URL = (
            self.aws_console_base_url
            + "/secretsmanager/secret?name={secret_name}"
        )
        TITLE_FORMAT = "{secret_name}"
        for secret in secrets:
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
