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


def check(network: Network) -> tuple[Finding, ...]:
    """Return one finding per NAT gateway and set of missing doors.

    A subnet with an explicit route table association uses that table.
    Every other subnet in the VPC uses the main route table.
    """
    explicit_ids: defaultdict[str, set[str]] = defaultdict(set)
    subnets_by_vpc: defaultdict[str, list[Subnet]] = defaultdict(list)
    for table in network.route_tables:
        explicit_ids[table.vpc_id].update(table.subnet_ids)
    for subnet in network.subnets:
        subnets_by_vpc[subnet.vpc_id].append(subnet)

    nat_names = {nat.id: nat.name for nat in network.nat_gateways}
    groups: defaultdict[tuple[str, tuple[Service, ...]], list[_Piece]] = defaultdict(
        list
    )

    for table in network.route_tables:
        nat_id = _nat_target(table)
        if nat_id is None:
            continue
        subnets = _subnets_for_table(table, subnets_by_vpc, explicit_ids)
        if not subnets:
            continue
        open_doors = _open_doors(table, network.gateway_endpoints)
        missing = tuple(service for service in _SERVICES if service not in open_doors)
        if not missing:
            continue
        groups[(nat_id, missing)].append(_Piece(table, subnets))

    findings: list[Finding] = []
    for (nat_id, missing), pieces in groups.items():
        subnet_by_id: dict[str, Subnet] = {}
        tables: dict[str, str | None] = {}
        for piece in pieces:
            tables[piece.table.id] = piece.table.name
            for subnet in piece.subnets:
                subnet_by_id[subnet.id] = subnet
        subnet_ids = set(subnet_by_id)
        lambda_count = sum(
            1
            for function in network.lambdas
            if subnet_ids.intersection(function.subnet_ids)
        )
        findings.append(
            Finding(
                nat_id=nat_id,
                nat_name=nat_names.get(nat_id),
                subnets=tuple(sorted(subnet_by_id.values(), key=_subnet_key)),
                route_tables=tuple(
                    sorted(
                        (
                            RouteTableRef(table_id, tables[table_id])
                            for table_id in tables
                        ),
                        key=lambda ref: _named_key(ref.name, ref.id),
                    )
                ),
                missing=missing,
                lambda_count=lambda_count,
            )
        )
    findings.sort(key=_finding_key)
    return tuple(findings)


class _Piece:
    def __init__(self, table: RouteTable, subnets: tuple[Subnet, ...]) -> None:
        self.table = table
        self.subnets = subnets


def _subnets_for_table(
    table: RouteTable,
    subnets_by_vpc: Mapping[str, Sequence[Subnet]],
    explicit_ids: Mapping[str, set[str]],
) -> tuple[Subnet, ...]:
    chosen: dict[str, Subnet] = {}
    explicit_here = set(table.subnet_ids)
    for subnet in subnets_by_vpc.get(table.vpc_id, ()):
        if subnet.id in explicit_here:
            chosen[subnet.id] = subnet
    if table.is_main:
        taken = explicit_ids.get(table.vpc_id, set())
        for subnet in subnets_by_vpc.get(table.vpc_id, ()):
            if subnet.id not in taken:
                chosen[subnet.id] = subnet
    return tuple(chosen.values())


def _nat_target(table: RouteTable) -> str | None:
    for route in table.routes:
        if (
            route.destination_cidr == "0.0.0.0/0"
            and route.state == "active"
            and route.nat_gateway_id
        ):
            return route.nat_gateway_id
    return None


def _open_doors(
    table: RouteTable, endpoints: Sequence[GatewayEndpoint]
) -> frozenset[Service]:
    """Services reached by an active route to an available gateway endpoint.

    An endpoint that only exists in the VPC, or only on another route table,
    is not a door for this table. A blackhole route is not a door either.
    """
    by_id = {endpoint.id: endpoint for endpoint in endpoints}
    open_services: set[Service] = set()
    for route in table.routes:
        if route.state != "active" or not route.gateway_id:
            continue
        endpoint = by_id.get(route.gateway_id)
        if endpoint is None or endpoint.state != "available":
            continue
        if endpoint.vpc_id != table.vpc_id:
            continue
        open_services.add(endpoint.service)
    return frozenset(open_services)


def _finding_key(finding: Finding) -> tuple[str, str, tuple[Service, ...]]:
    table_id = finding.route_tables[0].id if finding.route_tables else ""
    return (finding.nat_id, table_id, finding.missing)


def _subnet_key(subnet: Subnet) -> tuple[bool, str, str]:
    return _named_key(subnet.name, subnet.id)


def _named_key(name: str | None, id_: str) -> tuple[bool, str, str]:
    return (name is None, (name or "").casefold(), id_)
