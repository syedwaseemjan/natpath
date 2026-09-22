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


def read_network(
    region: str | None,
    profile: str | None,
    *,
    session_factory: Callable[..., Any] = boto3.Session,
) -> Network:
    try:
        session = session_factory(profile_name=profile, region_name=region)
    except ProfileNotFound as exc:
        raise NatpathError(str(exc)) from None
    resolved = session.region_name
    if not isinstance(resolved, str) or not resolved:
        raise NatpathError(
            "No AWS region is set. Pass --region or set AWS_DEFAULT_REGION."
        )
    try:
        return load_network(
            session.client("ec2"),
            session.client("lambda"),
            resolved,
        )
    except NoCredentialsError:
        raise NatpathError(
            "No AWS credentials found. Configure the AWS CLI or an instance role."
        ) from None
    except NoRegionError:
        raise NatpathError(
            "No AWS region is set. Pass --region or set AWS_DEFAULT_REGION."
        ) from None
    except EndpointConnectionError:
        raise NatpathError(
            "Could not reach AWS. Check the region and the network."
        ) from None
    except ClientError as exc:
        raise NatpathError(explain_client_error(exc)) from None


def explain_client_error(exc: ClientError) -> str:
    error = exc.response.get("Error", {})
    code = error.get("Code") or "Error"
    operation = exc.operation_name or "the AWS API"
    if code in _DENIED:
        return f"Cannot read the network: {operation} was denied ({code})."
    return f"AWS request failed: {operation} ({code})."


def _flag(args: argparse.Namespace, name: str) -> str | None:
    value = getattr(args, name, None)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise NatpathError(f"Internal error: --{name} was not a string.")
