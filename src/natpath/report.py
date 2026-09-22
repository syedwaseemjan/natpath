"""Render findings as plain text. Empty input renders as empty output."""

from collections.abc import Sequence

from natpath.model import Finding, Service

_ORDER: tuple[Service, ...] = ("s3", "dynamodb")
_LABELS: dict[Service, str] = {"s3": "S3", "dynamodb": "DynamoDB"}


def render(findings: Sequence[Finding]) -> str:
    if not findings:
        return ""
    return "\n\n".join(_render_finding(finding) for finding in findings) + "\n"


