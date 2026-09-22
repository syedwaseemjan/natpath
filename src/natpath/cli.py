"""Command line entry point. Reads AWS, prints findings, changes nothing."""

import argparse
import sys
from collections.abc import Callable, Sequence
from typing import Any

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    NoRegionError,
    ProfileNotFound,
)

from natpath import __version__
from natpath.check import check
from natpath.load import load_network
from natpath.model import Network
from natpath.report import render

_DENIED = frozenset({"UnauthorizedOperation", "AccessDenied", "AccessDeniedException"})


class NatpathError(Exception):
    """The command could not read the network."""


def main(
    argv: Sequence[str] | None = None,
    *,
    reader: Callable[..., Network] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="natpath",
        description=(
            "Report private subnets that send S3 or DynamoDB traffic through "
            "a NAT gateway because the free gateway endpoint is missing."
        ),
    )
    parser.add_argument(
        "--region",
        help="AWS region. Defaults to the region in your AWS configuration.",
    )
    parser.add_argument("--profile", help="Named AWS profile.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"natpath {__version__}",
    )
    args = parser.parse_args(argv)
    load = read_network if reader is None else reader
    try:
        network = load(_flag(args, "region"), _flag(args, "profile"))
        findings = check(network)
    except NatpathError as exc:
        print(exc, file=sys.stderr)
        return 2
    text = render(findings)
    if text:
        sys.stdout.write(text)
        return 1
    return 0


