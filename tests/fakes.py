"""In-memory paginators. Tests never call AWS."""

from typing import Any


class Paginator:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages
        self.calls: list[dict[str, Any]] = []

    def paginate(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        return self.pages


class FakeAws:
    def __init__(self, pages: dict[str, list[dict[str, Any]]]) -> None:
        self.paginators = {name: Paginator(page) for name, page in pages.items()}

    def get_paginator(self, name: str) -> Paginator:
        return self.paginators[name]


