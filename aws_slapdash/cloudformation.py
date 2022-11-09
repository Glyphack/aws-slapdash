import argparse
import json

from utils.aws import create_session
from utils.command import AWSServiceCommand
from utils.slapdash import Actions


class CloudformationCommand(AWSServiceCommand):
    def service_name(self):
        return "Cloud Formation"

    def service_url(self):
        return (
            self.aws_console_base_url
            + f"cloudformation/home?region={self.config.region}#/stacks/"
        )

    def serve_command(self, arg_parser: argparse.ArgumentParser):
        arg_parser.add_argument(
            "--stack-id",
        )
        args = arg_parser.parse_args()
        print(
            json.dumps(
                {
                    "view": {
                        "type": "list",
                        "options": self.serve_cloudformation(args.stack_id),
                    }
                }
            )
        )

    def serve_cloudformation(self, stack_name):
        if not stack_name:
            return self.list_stacks()

    def list_stacks(self):
        STACK_DETAILS_URL = (
            self.aws_console_base_url
            + f"cloudformation/home?region={self.config.region}#/stacks/"
            + "stackinfo?filteringStatus=active&filteringText=&viewNested=true"
            + "&hideStacks=false&stackId={stack_id}"
        )
        TITLE_FORMAT = "{stack_name} | {stack_status}"

        session = create_session()
        client = session.client("cloudformation")
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
                        "type": Actions.OPEN_URL,
                        "url": STACK_DETAILS_URL.format(stack_id=stack_id),
                    },
                }
            )
        return resp
