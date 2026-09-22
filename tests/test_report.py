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


