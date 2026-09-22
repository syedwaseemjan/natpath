"""Small builders for network facts. Tests pass these to the pure check."""

from collections.abc import Iterable

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


def subnet(id: str, vpc: str = "vpc-1", name: str | None = None) -> Subnet:
    return Subnet(id=id, vpc_id=vpc, name=name)


