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


