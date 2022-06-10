import re
from typing import Any, List, Set, TypeVar

from beanie import Document

DocumentType = TypeVar("DocumentType", bound="Document")


def normalize(value: str) -> str:
    if re.match(r'^\w+$', value):
        return value
    message = "Only alphanumerics and underscores names are allowed."
    raise ValueError(message)


def sort_by_index(cls, v) -> List[Any]:
    v.sort(key=lambda e: e.index)
    return v


async def get_entities(cls: Document, limit=100) -> List[DocumentType]:
    return await cls.find_many(limit=limit).to_list()


async def get_entity(cls: Document, **kwargs) -> DocumentType | None:
    return await cls.find_one(kwargs)


def get_object(cls: Document, gql_input) -> DocumentType:
    model_input = gql_input.to_pydantic()
    return cls.parse_obj(model_input)


async def create_entity(cls: Document, gql_input) -> DocumentType:
    obj = get_object(cls, gql_input)
    return await obj.insert()


async def update_entity(cls: Document, document_id, gql_input) -> DocumentType | None:
    entity = await get_entity(cls, id=document_id)
    if entity is None:
        return None
    model_input = get_object(cls, gql_input)
    return await entity.update(**model_input)


async def delete_entity(cls, document_id) -> DocumentType | None:
    entity = await get_entity(cls, id=document_id)
    if entity is None:
        return None
    await entity.delete()
    return entity
