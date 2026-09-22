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


def default_nat(nat_id: str, *, state: str = "active") -> Route:
    return route(cidr="0.0.0.0/0", nat=nat_id, state=state)


def endpoint_route(endpoint_id: str, *, state: str = "active") -> Route:
    return route(prefix="pl-1", gateway=endpoint_id, state=state)


def table(
    id: str,
    *,
    vpc: str = "vpc-1",
    name: str | None = None,
    is_main: bool = False,
    subnet_ids: Iterable[str] = (),
    routes: Iterable[Route] = (),
) -> RouteTable:
    return RouteTable(
        id=id,
        vpc_id=vpc,
        name=name,
        is_main=is_main,
        subnet_ids=tuple(subnet_ids),
        routes=tuple(routes),
    )


def endpoint(
    id: str,
    service: Service,
    route_table_ids: Iterable[str] = (),
    *,
    vpc: str = "vpc-1",
    state: str = "available",
) -> GatewayEndpoint:
    return GatewayEndpoint(
        id=id,
        vpc_id=vpc,
        service=service,
        state=state,
        route_table_ids=tuple(route_table_ids),
    )


def fn(name: str, subnet_ids: Iterable[str] = ()) -> LambdaFunction:
    return LambdaFunction(name=name, subnet_ids=tuple(subnet_ids))


