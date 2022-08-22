from typing import Optional

from strawberry import auto
from strawberry.experimental import pydantic

# === Complete Inputs ===
from dynamite.gql.types import ObjectId, ConditionValue
from dynamite.models import Topic, Detail, Report, ReportColumn, ConditionGroup, User, Condition


@pydantic.input(User)
class UserInput:
    username: auto
    password: auto


@pydantic.input(Detail)
class DetailInput:
    database_name: auto
    display_name: auto
    type: auto
    refers_to: Optional[ObjectId]


@pydantic.input(Topic)
class TopicInput:
    database_name: auto
    display_name: auto
    pivot: auto
    details: auto

@pydantic.input(ReportColumn)
class ReportColumnInput:
    database_name: auto
    display_name: auto
    index: auto
    detail: ObjectId


@pydantic.input(Condition)
class ConditionInput:
    operation: auto
    index: auto
    target: ObjectId
    value: ConditionValue


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

