import dataclasses
from typing import Optional, List

from strawberry import auto
from strawberry.experimental import pydantic

# === Complete Inputs ===
from gql.types import ObjectId
from models import Entity, Property, Report, ReportColumn, ConditionGroup, TableJoin, User, Condition
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


@pydantic.input(Entity, all_fields=True)
class EntityInput:
    properties: List[PropertyInput]

    def to_pydantic(self):
        data = dataclasses.asdict(self)
        data.pop("properties")
        return Entity(**data)
@pydantic.input(ReportColumn)
class ReportColumnInput:
    database_name: auto
    display_name: auto
    index: auto
    property: ObjectId

    def to_pydantic(self, **kwargs):
        data = dataclasses.asdict(self)
        property_id = data.pop("property")
        report_id = kwargs["report_id"]
        return ReportColumn.construct(report=link(Report, report_id), property=link(Property, property_id), **data)


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


@pydantic.input(TableJoin)
class TableJoinInput:
    type: auto
    columns: List[ObjectId]

    def to_pydantic(self):
        data = dataclasses.asdict(self)
        column_ids = data.pop("columns")
        return TableJoin(columns=link(Property, column_ids), **data)


@pydantic.input(Report, all_fields=True)
class ReportInput:
    columns: List[ReportColumnInput]

    def to_pydantic(self):
        data = dataclasses.asdict(self)
        data.pop("columns")
        return Report.construct(**data)
