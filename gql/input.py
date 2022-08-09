import dataclasses
from typing import Optional, List

from strawberry import auto
from strawberry.experimental import pydantic

# === Complete Inputs ===
from gql.types import ObjectId
from models import Entity, Property, Report, ReportColumn, ConditionGroup, User, Condition
from utils import link


@pydantic.input(User)
class UserInput:
    username: auto
    password: auto


@pydantic.input(Property)
class PropertyInput:
    database_name: auto
    display_name: auto
    type: auto
    refers_to: Optional[ObjectId]

    def to_pydantic(self, **kwargs):
        data = dataclasses.asdict(self)
        entity_id = kwargs["entity"]
        ref_id = data.pop('refers_to')
        entity = link(Entity, entity_id)
        reference = link(Property, ref_id)
        return Property.construct(refers_to=reference, entity=entity, **data)


@pydantic.input(Entity)
class EntityInput:
    database_name: auto
    display_name: auto
    pivot: auto
    properties: List[PropertyInput]

    def to_pydantic(self):
        data = dataclasses.asdict(self)
        data.pop("properties")
        return Entity.construct(**data)


@pydantic.input(ReportColumn)
class ReportColumnInput:
    database_name: auto
    display_name: auto
    index: auto
    property: ObjectId

    def to_pydantic(self, **kwargs):
        data = dataclasses.asdict(self)
        property_id = data.pop("property")
        return ReportColumn.construct(property=link(Property, property_id)[0], **data)


@pydantic.input(Condition)
class ConditionInput:
    operation: auto
    index: auto
    target: ObjectId
    value: auto

    async def to_pydantic(self):
        data = dataclasses.asdict(self)
        target_id = data.pop("target")
        return Condition.construct(target=link(Property, target_id), **data)


@pydantic.input(ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass


@pydantic.input(Report)
class ReportInput:
    columns: List[ReportColumnInput]
    database_name: auto
    display_name: auto
    condition_groups: auto
    root_operation: auto

    def to_pydantic(self):
        data = dataclasses.asdict(self)
        data.pop("columns")
        return Report.construct(**data)
