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


def network_from_descriptions(
    *,
    region: str,
    nat_gateways: Iterable[Mapping[str, Any]],
    subnets: Iterable[Mapping[str, Any]],
    route_tables: Iterable[Mapping[str, Any]],
    vpc_endpoints: Iterable[Mapping[str, Any]],
    functions: Iterable[Mapping[str, Any]],
) -> Network:
    """Build a Network from the shapes returned by the AWS APIs."""
    return Network(
        region=region,
        nat_gateways=tuple(_parse_all(nat_gateways, _parse_nat_gateway)),
        subnets=tuple(_parse_all(subnets, _parse_subnet)),
        route_tables=tuple(_parse_all(route_tables, _parse_route_table)),
        gateway_endpoints=tuple(_parse_all(vpc_endpoints, _parse_endpoint)),
        lambdas=tuple(_parse_all(functions, _parse_lambda)),
    )


