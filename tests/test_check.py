import pytest

from helpers import (
    default_nat,
    endpoint,
    endpoint_route,
    fn,
    nat_gateway,
    network,
    route,
    subnet,
    table,
)
from natpath.check import check
from natpath.load import network_from_descriptions
from natpath.model import RouteTableRef


def test_missing_doors_name_the_subnets_and_count_each_lambda_once() -> None:
    lambdas = [fn(f"job-{i}", ["subnet-a"]) for i in range(11)]
    lambdas.append(fn("shared", ["subnet-a", "subnet-b"]))
    lambdas.append(fn("other-net", ["subnet-other"]))
    found = check(
        network(
            nat_gateways=[nat_gateway("nat-abc", name="prod")],
            subnets=[
                subnet("subnet-b", name="app-b"),
                subnet("subnet-a", name="app-a"),
                subnet("subnet-other", vpc="vpc-9"),
            ],
            route_tables=[
                table(
                    "rtb-111",
                    name="private",
                    subnet_ids=["subnet-b", "subnet-a"],
                    routes=[
                        route(cidr="10.0.0.0/16", gateway="local"),
                        default_nat("nat-abc"),
                    ],
                )
            ],
            gateway_endpoints=[
                endpoint("vpce-elsewhere", "s3", ["rtb-other"], vpc="vpc-9"),
            ],
            lambdas=lambdas,
        )
    )

    assert len(found) == 1
    finding = found[0]
    assert finding.nat_id == "nat-abc"
    assert finding.nat_name == "prod"
    assert [item.id for item in finding.subnets] == ["subnet-a", "subnet-b"]
    assert finding.route_tables == (RouteTableRef("rtb-111", "private"),)
    assert finding.missing == ("s3", "dynamodb")
    assert finding.lambda_count == 12


def test_both_free_doors_on_the_route_are_quiet() -> None:
    found = check(
        network(
            nat_gateways=[nat_gateway()],
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-111",
                    is_main=True,
                    routes=[
                        default_nat("nat-abc"),
                        endpoint_route("vpce-s3"),
                        endpoint_route("vpce-ddb"),
                    ],
                )
            ],
            gateway_endpoints=[
                endpoint("vpce-s3", "s3", ["rtb-111"]),
                endpoint("vpce-ddb", "dynamodb", ["rtb-111"]),
            ],
            lambdas=[fn("job", ["subnet-a"])],
        )
    )
    assert found == ()


def test_active_route_is_the_door_when_the_association_list_is_empty() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-111",
                    subnet_ids=["subnet-a"],
                    routes=[
                        default_nat("nat-abc"),
                        endpoint_route("vpce-s3"),
                        endpoint_route("vpce-ddb"),
                    ],
                )
            ],
            gateway_endpoints=[
                endpoint("vpce-s3", "s3"),
                endpoint("vpce-ddb", "dynamodb"),
            ],
        )
    )
    assert found == ()


def test_an_endpoint_on_another_route_table_is_not_this_subnets_door() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-private",
                    subnet_ids=["subnet-a"],
                    routes=[default_nat("nat-abc")],
                ),
                table(
                    "rtb-other",
                    routes=[endpoint_route("vpce-s3"), endpoint_route("vpce-ddb")],
                ),
            ],
            gateway_endpoints=[
                endpoint("vpce-s3", "s3", ["rtb-other"]),
                endpoint("vpce-ddb", "dynamodb", ["rtb-other"]),
            ],
        )
    )
    assert len(found) == 1
    assert found[0].missing == ("s3", "dynamodb")
    assert [item.id for item in found[0].subnets] == ["subnet-a"]


def test_blackhole_route_is_not_a_door() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-111",
                    subnet_ids=["subnet-a"],
                    routes=[
                        default_nat("nat-abc"),
                        endpoint_route("vpce-s3", state="blackhole"),
                        endpoint_route("vpce-ddb"),
                    ],
                )
            ],
            gateway_endpoints=[
                endpoint("vpce-s3", "s3", ["rtb-111"]),
                endpoint("vpce-ddb", "dynamodb", ["rtb-111"]),
            ],
        )
    )
    assert len(found) == 1
    assert found[0].missing == ("s3",)


@pytest.mark.parametrize("state", ["pending", "deleted", "rejected", "failed"])
def test_endpoint_state_must_be_available(state: str) -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-111",
                    subnet_ids=["subnet-a"],
                    routes=[default_nat("nat-abc"), endpoint_route("vpce-s3")],
                )
            ],
            gateway_endpoints=[endpoint("vpce-s3", "s3", ["rtb-111"], state=state)],
        )
    )
    assert found[0].missing == ("s3", "dynamodb")


def test_endpoint_in_another_vpc_is_not_a_door() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-111",
                    subnet_ids=["subnet-a"],
                    routes=[default_nat("nat-abc"), endpoint_route("vpce-s3")],
                )
            ],
            gateway_endpoints=[endpoint("vpce-s3", "s3", ["rtb-111"], vpc="vpc-2")],
        )
    )
    assert found[0].missing == ("s3", "dynamodb")


def test_main_table_includes_only_subnets_without_an_explicit_association() -> None:
    found = check(
        network(
            nat_gateways=[nat_gateway()],
            subnets=[
                subnet("subnet-a", name="implicit"),
                subnet("subnet-b", name="explicit"),
            ],
            route_tables=[
                table("rtb-main", is_main=True, routes=[default_nat("nat-abc")]),
                table(
                    "rtb-custom",
                    subnet_ids=["subnet-b"],
                    routes=[
                        default_nat("nat-abc"),
                        endpoint_route("vpce-s3"),
                        endpoint_route("vpce-ddb"),
                    ],
                ),
            ],
            gateway_endpoints=[
                endpoint("vpce-s3", "s3", ["rtb-custom"]),
                endpoint("vpce-ddb", "dynamodb", ["rtb-custom"]),
            ],
        )
    )
    assert len(found) == 1
    assert [item.id for item in found[0].subnets] == ["subnet-a"]
    assert [item.id for item in found[0].route_tables] == ["rtb-main"]


def test_doors_on_the_main_table_do_not_cover_an_explicit_subnet() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-public"), subnet("subnet-private")],
            route_tables=[
                table(
                    "rtb-main",
                    is_main=True,
                    routes=[
                        route(cidr="0.0.0.0/0", gateway="igw-1"),
                        endpoint_route("vpce-s3"),
                        endpoint_route("vpce-ddb"),
                    ],
                ),
                table(
                    "rtb-private",
                    subnet_ids=["subnet-private"],
                    routes=[default_nat("nat-abc")],
                ),
            ],
            gateway_endpoints=[
                endpoint("vpce-s3", "s3", ["rtb-main"]),
                endpoint("vpce-ddb", "dynamodb", ["rtb-main"]),
            ],
        )
    )
    assert len(found) == 1
    assert [item.id for item in found[0].subnets] == ["subnet-private"]
    assert found[0].nat_id == "nat-abc"


def test_internet_gateway_default_route_is_quiet() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-main",
                    is_main=True,
                    routes=[route(cidr="0.0.0.0/0", gateway="igw-1")],
                )
            ],
        )
    )
    assert found == ()


def test_blackhole_nat_route_is_quiet() -> None:
    found = check(
        network(
            subnets=[subnet("subnet-a")],
            route_tables=[
                table(
                    "rtb-main",
                    is_main=True,
                    routes=[default_nat("nat-abc", state="blackhole")],
                )
            ],
        )
    )
    assert found == ()


def test_nat_with_no_subnets_is_quiet() -> None:
    found = check(
        network(
            nat_gateways=[nat_gateway()],
            route_tables=[
                table("rtb-main", is_main=True, routes=[default_nat("nat-abc")])
            ],
        )
    )
    assert found == ()


