from helpers import (
    default_nat,
    endpoint,
    endpoint_route,
    fn,
    nat_gateway,
    network,
    subnet,
    table,
)
from natpath.check import check
from natpath.model import Finding, RouteTableRef, Subnet
from natpath.report import render

STORY = """\
NAT gateway nat-abc (prod)
  These private subnets send all outside traffic through it:
    app-a (subnet-a)
    app-b (subnet-b)
  Route table:
    private (rtb-111)
  There is no free private door for S3.
  There is no free private door for DynamoDB.
  12 Lambdas run in these subnets.
  Their S3 and DynamoDB traffic is on the NAT bill.
  Adding the free doors takes that traffic off the bill.
"""


def test_story_prints_the_missing_doors_in_plain_words() -> None:
    lambdas = [fn(f"job-{i}", ["subnet-a"]) for i in range(11)]
    lambdas.append(fn("shared", ["subnet-a", "subnet-b"]))
    lambdas.append(fn("other-net", ["subnet-other"]))
    text = render(
        check(
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
                        subnet_ids=["subnet-a", "subnet-b"],
                        routes=[default_nat("nat-abc")],
                    )
                ],
                lambdas=lambdas,
            )
        )
    )
    assert text == STORY


def test_one_missing_door_names_only_that_service() -> None:
    text = render(
        check(
            network(
                subnets=[subnet("subnet-a")],
                route_tables=[
                    table(
                        "rtb-111",
                        subnet_ids=["subnet-a"],
                        routes=[default_nat("nat-abc"), endpoint_route("vpce-s3")],
                    )
                ],
                gateway_endpoints=[endpoint("vpce-s3", "s3", ["rtb-111"])],
                lambdas=[fn("job", ["subnet-a"])],
            )
        )
    )
    assert "There is no free private door for DynamoDB." in text
    assert "for S3." not in text
    assert "Their DynamoDB traffic is on the NAT bill." in text
    assert "Adding the free door takes that traffic off the bill." in text
    assert "1 Lambda runs in these subnets." in text
    assert "This private subnet sends all outside traffic through it:" in text


def test_no_lambdas_and_unnamed_resources() -> None:
    text = render(
        check(
            network(
                subnets=[subnet("subnet-a"), subnet("subnet-b")],
                route_tables=[
                    table(
                        "rtb-b",
                        subnet_ids=["subnet-b"],
                        routes=[default_nat("nat-abc")],
                    ),
                    table(
                        "rtb-a",
                        subnet_ids=["subnet-a"],
                        routes=[default_nat("nat-abc")],
                    ),
                ],
            )
        )
    )
    assert (
        text
        == """\
NAT gateway nat-abc
  These private subnets send all outside traffic through it:
    subnet-a
    subnet-b
  Route tables:
    rtb-a
    rtb-b
  There is no free private door for S3.
  There is no free private door for DynamoDB.
  No Lambdas run in these subnets.
  Their S3 and DynamoDB traffic is on the NAT bill.
  Adding the free doors takes that traffic off the bill.
"""
    )


