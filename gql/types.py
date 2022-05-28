from typing import List
from beanie import PydanticObjectId
from strawberry.experimental import pydantic
import models
import strawberry
from strawberry import auto

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
    description="String representation of column reference 'table.column'"
)
@pydantic.type(model=models.Join)
class JoinType:
    type: auto
    columns: List[List[ColumnReferenceNotationScaler]]

@pydantic.type(model=models.TableColumn, all_fields=True)
class TableColumnType:
    pass

@pydantic.type(models.Table, all_fields=True)
class TableType:
    pass


@pydantic.type(models.Condition)
class ConditionType:
    operation: auto
    index: auto
    target: ColumnReferenceNotationScaler
    value: auto
    
@pydantic.type(models.ConditionGroup)
class ConditionGroupType:
    operation: auto
    index: auto
    conditions: auto
    # condition_groups: "Optional[List[ConditionGroupType]]"


@pydantic.type(models.ReportColumn)
class ReportColumnType:
   index: auto
   ref_name: auto
   name: auto
   value: ColumnReferenceNotationScaler 

@pydantic.type(models.Report, all_fields=True)
class ReportType:
    @strawberry.field
    def query(self) -> str:
        query_builder = QueryBuilder()
        return query_builder.build(self)
