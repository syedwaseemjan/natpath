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


