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


