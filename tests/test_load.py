from fakes import ec2_client, lambda_client
from natpath.load import load_network, network_from_descriptions
from natpath.model import LambdaFunction


def test_pages_merge_and_only_s3_and_dynamodb_gateway_endpoints_are_kept() -> None:
    ec2 = ec2_client(
        nat_pages=[
            {"NatGateways": [_nat("nat-1", "prod")]},
            {"NatGateways": [_nat("nat-2"), {"NatGatewayId": "nat-missing-vpc"}]},
        ],
        subnets=[_subnet("subnet-a", "app-a"), {"VpcId": "vpc-1"}],
        route_tables=[_table()],
        vpc_endpoints=[
            _endpoint("vpce-s3", "com.amazonaws.eu-west-1.s3"),
            _endpoint("vpce-gov", "com.amazonaws.us-gov-west-1.s3"),
            _endpoint("vpce-cn", "cn.com.amazonaws.cn-north-1.dynamodb"),
            _endpoint("vpce-if", "com.amazonaws.eu-west-1.s3", type_="Interface"),
            _endpoint("vpce-sqs", "com.amazonaws.eu-west-1.sqs"),
        ],
    )
    functions = lambda_client(
        [
            {
                "FunctionName": "inside",
                "VpcConfig": {"SubnetIds": ["subnet-a", "subnet-a", " "]},
            },
            {"FunctionName": "outside"},
            {"FunctionName": "empty", "VpcConfig": {"SubnetIds": []}},
        ]
    )

    loaded = load_network(ec2, functions, "eu-west-1")

    assert loaded.region == "eu-west-1"
    assert [item.id for item in loaded.nat_gateways] == ["nat-1", "nat-2"]
    assert loaded.nat_gateways[0].name == "prod"
    assert loaded.subnets[0].name == "app-a"
    assert [item.id for item in loaded.gateway_endpoints] == [
        "vpce-s3",
        "vpce-gov",
        "vpce-cn",
    ]
    assert [item.service for item in loaded.gateway_endpoints] == [
        "s3",
        "s3",
        "dynamodb",
    ]
    assert loaded.gateway_endpoints[0].route_table_ids == ("rtb-111",)
    assert loaded.lambdas == (LambdaFunction("inside", ("subnet-a",)),)
    assert ec2.paginators["describe_vpc_endpoints"].calls == [
        {"Filters": [{"Name": "vpc-endpoint-type", "Values": ["Gateway"]}]}
    ]
    assert ec2.paginators["describe_subnets"].calls == [{}]


