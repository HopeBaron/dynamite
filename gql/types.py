from strawberry.experimental import pydantic
import models
import strawberry
from strawberry import auto
import bson

from query import sql_query

ObjectIdScalar = strawberry.scalar(
    bson.ObjectId,
    serialize=lambda v: str(v),
    parse_value=lambda v: bson.ObjectId(v),
    description="MongoDB ObjectId"
)


@pydantic.type(model=models.TableColumn, all_fields=True)
class TableColumn:
    pass


@pydantic.type(models.Table, all_fields=True)
class Table:
    pass



@pydantic.type(models.Condition, all_fields=True)
class Condition:
    pass


@pydantic.type(models.ConditionGroup, all_fields=True)
class ConditionGroup:
    pass


@pydantic.type(models.ReportColumn, all_fields=True)
class ReportColumn:
    pass

@pydantic.type(models.Report, all_fields=True)
class Report:
    @strawberry.field
    def query(self) -> str:
        return sql_query(self)
