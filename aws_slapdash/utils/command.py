from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser

from utils.aws import Config


class AWSServiceCommand(metaclass=ABCMeta):
    def __init__(self, config: Config):
        self.config = config

    @abstractmethod
    def service_name(self):
        raise NotImplementedError

    @abstractmethod
    def serve_command(self, arg_parser: ArgumentParser):
        raise NotImplementedError

    @abstractmethod
    def service_url(self):
        raise NotImplementedError

    @property
    def aws_console_base_url(self) -> str:
        return f"https://{self.config.region}.console.aws.amazon.com/"
