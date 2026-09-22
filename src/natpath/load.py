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


def load_network(ec2: Any, lambda_client: Any, region: str) -> Network:
    """Read one region through the AWS paginators and return a Network."""
    return network_from_descriptions(
        region=region,
        nat_gateways=_collect(ec2, "describe_nat_gateways", "NatGateways"),
        subnets=_collect(ec2, "describe_subnets", "Subnets"),
        route_tables=_collect(ec2, "describe_route_tables", "RouteTables"),
        vpc_endpoints=_collect(
            ec2,
            "describe_vpc_endpoints",
            "VpcEndpoints",
            Filters=_GATEWAY_FILTER,
        ),
        functions=_collect(lambda_client, "list_functions", "Functions"),
    )


