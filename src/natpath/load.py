"""Load VPC and Lambda facts. This module does not decide what is wrong."""

from collections.abc import Iterable, Mapping
from typing import Any

from natpath.model import (
    GatewayEndpoint,
    LambdaFunction,
    NatGateway,
    Network,
    Route,
    RouteTable,
    Service,
    Subnet,
)

_GATEWAY_FILTER = [{"Name": "vpc-endpoint-type", "Values": ["Gateway"]}]


