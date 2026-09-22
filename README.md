# natpath

A read-only command that tells you when private subnets send S3 and DynamoDB traffic through a NAT gateway.

NAT data processing is billed for every byte. The gateway endpoints for S3 and DynamoDB are free. They add a route for those two services, so that traffic never reaches the NAT. Traffic to the rest of the internet still does. If the route table behind the NAT does not have those endpoints, S3 and DynamoDB bytes from those subnets are on the NAT bill. The cost page shows the amount. This command shows the route tables and subnets that cause it.

You run it, add the missing gateway endpoints on the printed route tables, and run it again until it prints nothing.

## Run

```bash
pip install .
natpath
natpath --region us-east-1
natpath --profile prod
```

It reads one region: the region in your AWS configuration, or the one you pass with `--region`. It uses the credentials you already have. It does not change the network, and it does not read Cost Explorer.

A quiet run prints nothing and exits 0. A missing door prints the finding and exits 1. Exit 2 means AWS could not be read.

## Example

```text
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
```

For each printed route table, add a gateway endpoint for S3 and a gateway endpoint for DynamoDB, then run `natpath` again. Choose the gateway endpoint type. The interface type is a separate PrivateLink service, and this traffic stays on the NAT until the gateway type is on the route.

The door covers S3 and DynamoDB in this region. Calls to another region still use the NAT. The hourly NAT charge is unchanged. The command cannot see how many bytes moved. It sees the path: anything in these subnets that calls those services in this region is paying the NAT data charge for those bytes.

## Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeNatGateways",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcEndpoints",
        "lambda:ListFunctions"
      ],
      "Resource": "*"
    }
  ]
}
```

## What it treats as a free door

A route table sends outside traffic through a NAT when it has an active `0.0.0.0/0` route to that NAT gateway. The subnets on that table are the ones listed. A subnet with an explicit association uses that table. Every other subnet in the VPC uses the main route table.

A free door is an active route to an available gateway endpoint for that service. An endpoint that exists only on some other route table does not count. A blackhole route does not count. The Lambda line is how many functions have a VPC subnet in that set. The finding is the missing door, including when the count is zero, because other workloads in those subnets use the same path.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check src tests && ruff format --check src tests && mypy && pytest
```
