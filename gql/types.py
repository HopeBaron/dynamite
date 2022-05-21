from typing import Dict, List, Optional
from beanie import PydanticObjectId
from strawberry.experimental import pydantic
import models
import strawberry
from strawberry import LazyType, auto
import bson

from query import QueryBuilder

ObjectIdScalar = strawberry.scalar(
    PydanticObjectId,
    serialize=lambda v: str(v),
    parse_value=lambda v: PydanticObjectId(v),
    description="MongoDB ObjectId"
)

ColumnReferenceNotationScaler = strawberry.scalar(
    models.ColumnReferenceNotation,
    serialize=lambda v: str(v),
    parse_value=lambda v: models.ColumnReferenceNotation.ref(v),
    description="String reperenting a colmn refrence in the form of 'table.column'"
)


@pydantic.type(model=models.TableColumn, all_fields=True)
class TableColumnType:
    pass


@pydantic.type(models.Table, all_fields=True)
class TableType:
    pass


@pydantic.type(models.Condition, all_fields=True)
class ConditionType:
    pass


@pydantic.type(models.ConditionGroup)
class ConditionGroupType:
    operation: auto
    sequence: auto
    conditions: auto
    # condition_groups: "Optional[List[ConditionGroupType]]"


@pydantic.type(models.ReportColumn, all_fields=True)
class ReportColumnType:
    pass


@pydantic.type(models.Report, all_fields=True)
class ReportType:
    @strawberry.field
    def query(self) -> str:
        query_builder = QueryBuilder()
        return query_builder.sql_query(self)
