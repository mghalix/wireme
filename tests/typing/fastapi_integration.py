from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Annotated, assert_type

from fastapi import FastAPI

from wireme import wired
from wireme.fastapi import FromWeb, override_web_dependency


class Service:
    pass


def get_service() -> Service:
    return Service()


async def get_async_service() -> Service:
    return Service()


def get_service_resource() -> Iterator[Service]:
    yield Service()


async def get_async_service_resource() -> AsyncIterator[Service]:
    yield Service()


type ServiceDep = Annotated[
    Service,
    wired(get_service),
]

type AsyncServiceDep = Annotated[
    Service,
    wired(get_async_service),
]

type ResourceServiceDep = Annotated[
    Service,
    wired(get_service_resource),
]

type AsyncResourceServiceDep = Annotated[
    Service,
    wired(get_async_service_resource),
]


def plain_route(service: FromWeb[Service]) -> None:
    assert_type(service, Service)


def aliased_route(service: FromWeb[ServiceDep]) -> None:
    assert_type(service, Service)


def async_aliased_route(service: FromWeb[AsyncServiceDep]) -> None:
    assert_type(service, Service)


def resource_route(service: FromWeb[ResourceServiceDep]) -> None:
    assert_type(service, Service)


def async_resource_route(service: FromWeb[AsyncResourceServiceDep]) -> None:
    assert_type(service, Service)


def replacement_with_different_parameters(flag: bool = True) -> Service:
    _ = flag
    return Service()


def generator_replacement() -> Iterator[Service]:
    yield Service()


async def async_generator_replacement() -> AsyncIterator[Service]:
    yield Service()


app = FastAPI()

with override_web_dependency(app, get_service, replacement_with_different_parameters):
    pass

with override_web_dependency(app, get_service, generator_replacement):
    pass

with override_web_dependency(app, get_service, async_generator_replacement):
    pass

with override_web_dependency(app, get_service, get_async_service):
    pass
