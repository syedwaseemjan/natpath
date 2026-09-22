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


