import re
from typing import Any, List, TypeVar

from beanie import Document, Link
from bson import DBRef
from strawberry.utils.await_maybe import await_maybe

from dynamite.errors import DynamiteError, DynamiteErrorTypes

DocumentType = TypeVar("DocumentType", bound="Document")


def normalize(value: str) -> str:
    if re.match(r'^\w+$', value):
        return value
    message = "Only alphanumerics and underscores names are allowed."
    raise DynamiteError(DynamiteErrorTypes.DISALLOWED_CHARACTERS, message)


def sort_by_index(cls, value) -> List[Any]:
    value.sort(key=lambda e: e.index)
    return value






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
