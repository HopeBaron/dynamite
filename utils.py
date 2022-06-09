
import re
from typing import Any, List, Set

import bcrypt
from beanie import Document



def normalize(value: str) -> str:
    if re.match(r'^[A-Za-z0-9_]+$', value):
        return value
    message = "Only alphanumerics and underscores names are allowed."
    raise ValueError(message)


def sort_by_index(cls, v) -> List[Any]:
    v.sort(key=lambda e: e.index)
    return v



async def get_entities(cls: Document, limit=100) -> List[Document]:
    return await cls.find_many(limit=limit).to_list()


async def get_entity(cls: Document, **kwargs) -> Document:
    return await cls.find_one(kwargs)


def get_object(cls: Document, input) -> Document:
    model_input = input.to_pydantic()
    return cls.parse_obj(model_input)


async def create_entity(cls: Document, input) -> Document:
    obj = get_object(cls, input)
    return await obj.insert()


async def update_entity(cls: Document, id, input) -> Document:
    entity = get_entity(cls, id=id)
    if entity is None:
        return None
    modelized_input = get_object(cls, input)
    await entity.update(Set(**modelized_input))


async def delete_entity(cls, id):
    entity = await get_entity(cls, id=id)
    if entity is None:
        return None
    await entity.delete()
    return entity
