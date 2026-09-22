"""Render findings as plain text. Empty input renders as empty output."""

from collections.abc import Sequence

from natpath.model import Finding, Service

_ORDER: tuple[Service, ...] = ("s3", "dynamodb")
_LABELS: dict[Service, str] = {"s3": "S3", "dynamodb": "DynamoDB"}


def render(findings: Sequence[Finding]) -> str:
    if not findings:
        return ""
    return "\n\n".join(_render_finding(finding) for finding in findings) + "\n"


def _render_finding(finding: Finding) -> str:
    lines = [_nat_heading(finding)]
    if len(finding.subnets) == 1:
        lines.append("  This private subnet sends all outside traffic through it:")
    else:
        lines.append("  These private subnets send all outside traffic through it:")
    lines.extend(f"    {_label(subnet.name, subnet.id)}" for subnet in finding.subnets)
    if len(finding.route_tables) == 1:
        lines.append("  Route table:")
    else:
        lines.append("  Route tables:")
    lines.extend(
        f"    {_label(table.name, table.id)}" for table in finding.route_tables
    )
    for service in _ordered(finding.missing):
        lines.append(f"  There is no free private door for {_LABELS[service]}.")
    lines.append(f"  {_lambda_sentence(finding.lambda_count)}")
    traffic, fix = _closing(finding.missing)
    lines.append(f"  {traffic}")
    lines.append(f"  {fix}")
    return "\n".join(lines)


def _nat_heading(finding: Finding) -> str:
    name = _shown(finding.nat_name)
    if name:
        return f"NAT gateway {finding.nat_id} ({name})"
    return f"NAT gateway {finding.nat_id}"


def _lambda_sentence(count: int) -> str:
    if count == 0:
        return "No Lambdas run in these subnets."
    if count == 1:
        return "1 Lambda runs in these subnets."
    return f"{count} Lambdas run in these subnets."


