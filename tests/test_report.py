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


