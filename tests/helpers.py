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


def nat_gateway(
    id: str = "nat-abc",
    vpc: str = "vpc-1",
    name: str | None = None,
    state: str = "available",
) -> NatGateway:
    return NatGateway(id=id, vpc_id=vpc, name=name, state=state)


def route(
    *,
    cidr: str | None = None,
    prefix: str | None = None,
    nat: str | None = None,
    gateway: str | None = None,
    state: str = "active",
) -> Route:
    return Route(
        destination_cidr=cidr,
        destination_prefix_list_id=prefix,
        nat_gateway_id=nat,
        gateway_id=gateway,
        state=state,
    )


