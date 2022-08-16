import dataclasses
import re
from typing import Any, List, TypeVar, Tuple, Iterable

from beanie import Document, Link
from bson import DBRef
from six import string_types
from strawberry.experimental.pydantic.conversion import convert_strawberry_class_to_pydantic_model
from strawberry.utils.await_maybe import await_maybe

from enums import ConditionGroupOperations

DocumentType = TypeVar("DocumentType", bound="Document")


def normalize(value: str) -> str:
    if re.match(r'^\w+$', value):
        return value
    message = "Only alphanumerics and underscores names are allowed."
    raise ValueError(message)


def sort_by_index(cls, value) -> List[Any]:
    value.sort(key=lambda e: e.index)
    return value


async def get_models(cls: Document, limit=100) -> List[DocumentType]:
    return await cls.find_many(limit=limit, fetch_links=True).to_list()


async def get_model(cls: Document, **kwargs) -> DocumentType | None:
    return await cls.find_one(kwargs, fetch_links=True)


async def create_model(gql_input, **kwargs) -> DocumentType:
    obj = await await_maybe(gql_input.to_pydantic(**kwargs))
    return await obj.insert()


async def create_models(gql_input, **kwargs) -> List[DocumentType]:
    return [await create_model(form, **kwargs) for form in gql_input]


def partition(pred, iterable):
    trues = []
    falses = []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses


def link(cls: Document, *ids):
    return [Link(DBRef(cls.get_motor_collection().name, id), cls) for id in ids]
