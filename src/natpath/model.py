"""Facts about a network, and the missing free doors found in it."""

from dataclasses import dataclass
from typing import Literal

Service = Literal["s3", "dynamodb"]


@dataclass(frozen=True, slots=True)
class Subnet:
    id: str
    vpc_id: str
    name: str | None


