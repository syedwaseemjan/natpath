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


def _collect(client: Any, operation: str, key: str, **kwargs: Any) -> list[Any]:
    paginator = client.get_paginator(operation)
    items: list[Any] = []
    for page in paginator.paginate(**kwargs):
        batch = page.get(key, [])
        if isinstance(batch, list):
            items.extend(batch)
    return items


def _parse_all(items: Iterable[Mapping[str, Any]], parse: Any) -> list[Any]:
    parsed: list[Any] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        value = parse(item)
        if value is not None:
            parsed.append(value)
    return parsed


def _parse_nat_gateway(item: Mapping[str, Any]) -> NatGateway | None:
    nat_id = _text(item.get("NatGatewayId"))
    vpc_id = _text(item.get("VpcId"))
    if nat_id is None or vpc_id is None:
        return None
    return NatGateway(
        id=nat_id,
        vpc_id=vpc_id,
        name=_name(item),
        state=_text(item.get("State")) or "",
    )


def _parse_subnet(item: Mapping[str, Any]) -> Subnet | None:
    subnet_id = _text(item.get("SubnetId"))
    vpc_id = _text(item.get("VpcId"))
    if subnet_id is None or vpc_id is None:
        return None
    return Subnet(id=subnet_id, vpc_id=vpc_id, name=_name(item))


def _parse_route_table(item: Mapping[str, Any]) -> RouteTable | None:
    table_id = _text(item.get("RouteTableId"))
    vpc_id = _text(item.get("VpcId"))
    if table_id is None or vpc_id is None:
        return None
    subnet_ids: list[str] = []
    is_main = False
    associations = item.get("Associations") or []
    if isinstance(associations, list):
        for assoc in associations:
            if not isinstance(assoc, Mapping) or not _association_active(assoc):
                continue
            if assoc.get("Main") is True:
                is_main = True
            subnet_id = _text(assoc.get("SubnetId"))
            if subnet_id is not None:
                subnet_ids.append(subnet_id)
    routes: list[Route] = []
    raw_routes = item.get("Routes") or []
    if isinstance(raw_routes, list):
        for raw in raw_routes:
            if isinstance(raw, Mapping):
                routes.append(_parse_route(raw))
    return RouteTable(
        id=table_id,
        vpc_id=vpc_id,
        name=_name(item),
        is_main=is_main,
        subnet_ids=_unique(subnet_ids),
        routes=tuple(routes),
    )


def _parse_route(item: Mapping[str, Any]) -> Route:
    return Route(
        destination_cidr=_text(item.get("DestinationCidrBlock")),
        destination_prefix_list_id=_text(item.get("DestinationPrefixListId")),
        nat_gateway_id=_text(item.get("NatGatewayId")),
        gateway_id=_text(item.get("GatewayId")),
        state=_text(item.get("State")) or "",
    )


