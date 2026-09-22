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


