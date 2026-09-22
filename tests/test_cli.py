import pytest
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

from fakes import ec2_client, lambda_client
from helpers import default_nat, network, subnet, table
from natpath.check import check
from natpath.cli import NatpathError, main, read_network
from natpath.model import Network
from natpath.report import render


def test_findings_go_to_stdout_and_exit_1(capsys: pytest.CaptureFixture[str]) -> None:
    loaded = network(
        subnets=[subnet("subnet-a", name="app")],
        route_tables=[
            table(
                "rtb-1",
                name="private",
                subnet_ids=["subnet-a"],
                routes=[default_nat("nat-abc")],
            )
        ],
    )

    def reader(region: str | None, profile: str | None) -> Network:
        return loaded

    assert main([], reader=reader) == 1
    captured = capsys.readouterr()
    assert captured.out == render(check(loaded))
    assert captured.err == ""


def test_a_clean_network_prints_nothing_and_exits_0(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def reader(region: str | None, profile: str | None) -> Network:
        return network()

    assert main([], reader=reader) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_region_and_profile_are_forwarded() -> None:
    seen: dict[str, str | None] = {}

    def reader(region: str | None, profile: str | None) -> Network:
        seen["region"] = region
        seen["profile"] = profile
        return network()

    assert main(["--region", "eu-west-1", "--profile", "prod"], reader=reader) == 0
    assert seen == {"region": "eu-west-1", "profile": "prod"}


def test_a_read_error_goes_to_stderr_and_exits_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def reader(region: str | None, profile: str | None) -> Network:
        raise NatpathError(
            "Cannot read the network: DescribeNatGateways was denied "
            "(UnauthorizedOperation)."
        )

    assert main([], reader=reader) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "DescribeNatGateways was denied" in captured.err


def test_help_and_version_exit_0() -> None:
    with pytest.raises(SystemExit) as help_exit:
        main(["--help"])
    assert help_exit.value.code == 0
    with pytest.raises(SystemExit) as version_exit:
        main(["--version"])
    assert version_exit.value.code == 0


def test_missing_region_does_not_call_aws() -> None:
    class Session:
        region_name = None

        def client(self, name: str) -> object:
            raise AssertionError(name)

    with pytest.raises(NatpathError, match="No AWS region"):
        read_network(None, None, session_factory=lambda **kwargs: Session())


def test_unknown_profile_is_reported() -> None:
    def factory(**kwargs: object) -> object:
        raise ProfileNotFound(profile="prod")

    with pytest.raises(NatpathError, match="prod"):
        read_network("us-east-1", "prod", session_factory=factory)


def test_denied_api_names_the_operation() -> None:
    class Boom:
        def paginate(self, **kwargs: object) -> object:
            raise ClientError(
                {"Error": {"Code": "UnauthorizedOperation", "Message": "no"}},
                "DescribeRouteTables",
            )

    class Client:
        def get_paginator(self, name: str) -> Boom:
            return Boom()

    class Session:
        region_name = "us-east-1"

        def client(self, name: str) -> Client:
            return Client()

    with pytest.raises(NatpathError, match="DescribeRouteTables was denied"):
        read_network("us-east-1", None, session_factory=lambda **kwargs: Session())


def test_missing_credentials_are_reported() -> None:
    class Boom:
        def paginate(self, **kwargs: object) -> object:
            raise NoCredentialsError()

    class Client:
        def get_paginator(self, name: str) -> Boom:
            return Boom()

    class Session:
        region_name = "us-east-1"

        def client(self, name: str) -> Client:
            return Client()

    with pytest.raises(NatpathError, match="No AWS credentials"):
        read_network("us-east-1", None, session_factory=lambda **kwargs: Session())


def test_read_network_uses_the_session_clients() -> None:
    ec2 = ec2_client(nat_gateways=[{"NatGatewayId": "nat-abc", "VpcId": "vpc-1"}])
    functions = lambda_client()

    class Session:
        region_name = "eu-west-1"

        def client(self, name: str) -> object:
            if name == "ec2":
                return ec2
            if name == "lambda":
                return functions
            raise AssertionError(name)

    loaded = read_network(
        "eu-west-1",
        "prod",
        session_factory=lambda **kwargs: Session(),
    )
    assert loaded.region == "eu-west-1"
    assert [item.id for item in loaded.nat_gateways] == ["nat-abc"]
