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


