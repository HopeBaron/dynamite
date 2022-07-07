import re
from typing import Any, List, TypeVar, Tuple

from beanie import Document
from sql import Table, Expression

from enums import ConditionGroupOperations, ColumnJoins, WhereOperations

DocumentType = TypeVar("DocumentType", bound="Document")


def normalize(value: str) -> str:
    if re.match(r'^\w+$', value):
        return value
    message = "Only alphanumerics and underscores names are allowed."
    raise ValueError(message)


def sort_by_index(cls, value) -> List[Any]:
    value.sort(key=lambda e: e.index)
    return value


async def get_entities(cls: Document, limit=100) -> List[DocumentType]:
    return await cls.find_many(limit=limit).to_list()


async def get_entity(cls: Document, **kwargs) -> DocumentType | None:
    return await cls.find_one(kwargs)


async def create_entity(cls: Document, gql_input) -> DocumentType:
    obj = gql_input.to_pydantic()
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


def reduce_conditions(acc, last_part, operator=ConditionGroupOperations.AND):
    if not isinstance(acc, Tuple):
        condition = acc == last_part
        return condition, last_part
    old_condition, old_last_part = acc
    (new_condition, _) = reduce_conditions(old_last_part, last_part)
    condition_group_or_single = acc.operation or operator
    mapped_function = group_operators_dict[condition_group_or_single]
    combination = mapped_function(old_condition, new_condition)
    return combination, last_part


joins_dict = {
    ColumnJoins.INNER: Table.join,
    ColumnJoins.LEFT: Table.left_join,
    ColumnJoins.RIGHT: Table.right_join
}

group_operators_dict = {
    ConditionGroupOperations.AND: Expression.__and__,
    ConditionGroupOperations.OR: Expression.__or__,
}

operators_dict = {
    WhereOperations.EQ: Expression.__eq__,
    WhereOperations.GT: Expression.__gt__,
    WhereOperations.LT: Expression.__lt__,
    WhereOperations.LTE: Expression.__le__,
    WhereOperations.GTE: Expression.__ge__,
    WhereOperations.IN: Expression.in_,
    WhereOperations.NEQ: Expression.__ne__
}
