"""Decide which NAT-backed subnets are missing a free S3 or DynamoDB door."""

from collections import defaultdict
from collections.abc import Mapping, Sequence

from natpath.model import (
    Finding,
    GatewayEndpoint,
    Network,
    RouteTable,
    RouteTableRef,
    Service,
    Subnet,
)

_SERVICES: tuple[Service, ...] = ("s3", "dynamodb")


