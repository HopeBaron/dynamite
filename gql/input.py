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


@pydantic.input(Entity)
class EntityInput:
    database_name: auto
    display_name: auto
    pivot: auto
    properties: auto

@pydantic.input(ReportColumn)
class ReportColumnInput:
    database_name: auto
    display_name: auto
    index: auto
    prop: ObjectId


@pydantic.input(Condition)
class ConditionInput:
    operation: auto
    index: auto
    target: ObjectId
    value: auto


@pydantic.input(ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass


@pydantic.input(Report)
class ReportInput:
    columns: auto
    database_name: auto
    display_name: auto
    condition_groups: auto
    root_operation: auto

