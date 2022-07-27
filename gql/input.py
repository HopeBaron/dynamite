import dataclasses
from typing import Optional, List

import strawberry
from strawberry import auto
from strawberry.experimental import pydantic

from gql.dataloaders import property_loader
from models import Entity, Property, Report, ReportColumn, ConditionGroup, TableJoin, User, Condition

# === Complete Inputs ===
from gql.types import ObjectId
from models import Entity, Property, Report, ReportColumn, ConditionGroup, TableJoin, User, Condition


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

    async def to_pydantic(self):
        data = dataclasses.asdict(self)
        entity_id = data.pop("entity")
        ref_id = data.pop('refers_to')
        entity = await Entity.get(entity_id)
        reference = None if ref_id is None else await Property.get(ref_id)
        return Property(refers_to=reference, entity=entity, **data)


@pydantic.input(Entity, all_fields=True)
class EntityInput:
    properties: List[PropertyInput]

@pydantic.input(ReportColumn)
class ReportColumnInput:
    database_name: auto
    display_name: auto
    index: auto
    property: ObjectId

    async def to_pydantic(self):
        data = dataclasses.asdict(self)
        report_id = data.pop("report")
        property_id = data.pop("property")
        report = await Report.get(report_id)
        prop = await Property.get(property_id)
        return ReportColumn(report=report, property=prop, **data)

@pydantic.input(Condition)
class ConditionInput:
    operation: auto
    index: auto
    target: ObjectId
    value: auto

    async def to_pydantic(self):
        data = dataclasses.asdict(self)
        target_id = data.pop("target")
        prop = Property.get(target_id)
        return Condition(target=prop, **data)

@pydantic.input(ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass

@pydantic.input(TableJoin)
class TableJoinInput:
    type: auto
    columns: List[ObjectId]

    async def to_pydantic(self):
        data = dataclasses.asdict(self)
        column_ids = data.pop("columns")
        props = property_loader.load(column_ids)
        return TableJoin(columns=props, **data)


@pydantic.input(Report, all_fields=True)
class ReportInput:
    columns: List[ReportColumnInput]