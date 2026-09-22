"""Facts about a network, and the missing free doors found in it."""

from dataclasses import dataclass
from typing import Literal

Service = Literal["s3", "dynamodb"]


@dataclass(frozen=True, slots=True)
class Subnet:
    id: str
    vpc_id: str
    name: str | None


@dataclass(frozen=True, slots=True)
class Route:
    destination_cidr: str | None
    destination_prefix_list_id: str | None
    nat_gateway_id: str | None
    gateway_id: str | None
    state: str


@dataclass(frozen=True, slots=True)
class RouteTable:
    id: str
    vpc_id: str
    name: str | None
    is_main: bool
    subnet_ids: tuple[str, ...]
    routes: tuple[Route, ...]


@dataclass(frozen=True, slots=True)
class GatewayEndpoint:
    """A gateway VPC endpoint for S3 or DynamoDB.

    The free door is an active route on a route table whose gateway id is
    this endpoint. route_table_ids is the association list from AWS. The
    route is what steers the traffic.
    """

    id: str
    vpc_id: str
    service: Service
    state: str
    route_table_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NatGateway:
    id: str
    vpc_id: str
    name: str | None
    state: str


@dataclass(frozen=True, slots=True)
class LambdaFunction:
    name: str
    subnet_ids: tuple[str, ...]


