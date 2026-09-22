"""In-memory paginators. Tests never call AWS."""

from typing import Any


class Paginator:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages
        self.calls: list[dict[str, Any]] = []

    def paginate(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        return self.pages


class FakeAws:
    def __init__(self, pages: dict[str, list[dict[str, Any]]]) -> None:
        self.paginators = {name: Paginator(page) for name, page in pages.items()}

    def get_paginator(self, name: str) -> Paginator:
        return self.paginators[name]


def ec2_client(
    *,
    nat_gateways: list[dict[str, Any]] | None = None,
    subnets: list[dict[str, Any]] | None = None,
    route_tables: list[dict[str, Any]] | None = None,
    vpc_endpoints: list[dict[str, Any]] | None = None,
    nat_pages: list[dict[str, Any]] | None = None,
    endpoint_pages: list[dict[str, Any]] | None = None,
) -> FakeAws:
    return FakeAws(
        {
            "describe_nat_gateways": nat_pages
            if nat_pages is not None
            else [{"NatGateways": nat_gateways or []}],
            "describe_subnets": [{"Subnets": subnets or []}],
            "describe_route_tables": [{"RouteTables": route_tables or []}],
            "describe_vpc_endpoints": endpoint_pages
            if endpoint_pages is not None
            else [{"VpcEndpoints": vpc_endpoints or []}],
        }
    )


