from typing import List, Optional, Dict, Any, TypeVar, Union

import strawberry
from beanie import PydanticObjectId
from strawberry import auto, LazyType
from strawberry.experimental import pydantic

from dynamite import models, errors
from dynamite.enums import DetailExpectedType, WhereOperations
from dynamite.errors import DynamiteErrorTypes
from dynamite.gql.dataloaders import report_loader, detail_loader
from dynamite.models import Query, Detail, Report
# === Scalers ===
from dynamite.transformer import SqlTransformer


@strawberry.type
class DynamiteErrorType:
    message: str
    code: DynamiteErrorTypes


T = TypeVar("T")

DynamiteResult = Union[T, DynamiteErrorType]

ObjectId = strawberry.scalar(
    PydanticObjectId,
    serialize=lambda v: str(v),
    parse_value=lambda v: PydanticObjectId(v),
    description="MongoDB ObjectId"
)

ConditionValue = strawberry.scalar(
    Any,
    serialize=lambda v: v,
    parse_value=lambda v: v,
    description="Condition Value"
)


# === Authentication models ===

@pydantic.type(model=models.User)
class UserType:
    username: auto


@strawberry.type
class LoginSuccess:
    user: UserType
    token: str


# === Domain models ===
@strawberry.type
class PermittedOperation:
    type: DetailExpectedType
    operations: List[WhereOperations]
@pydantic.type(models.Detail)
class DetailType:
    id: ObjectId
    type: auto
    display_name: auto
    database_name: auto

    @strawberry.field
    async def references(self) -> List["DetailType"]:
        detail: Detail = await detail_loader.load(self.id)
        return await detail.references.to_list()

    @strawberry.field
    async def refers_to(self) -> Optional["DetailType"]:
        detail: Detail = await detail_loader.load(self.id)
        return await detail.fetched_refers_to()


@pydantic.type(models.Topic)
class TopicType:
    id: ObjectId
    details: List["DetailType"]
    pivot: auto
    display_name: auto
    database_name: auto
    owner: UserType


@pydantic.type(models.Condition)
class ConditionType:
    id: auto
    operation: auto
    index: auto
    value: ConditionValue
    target: ObjectId

    async def target_object(self):
        return await detail_loader.load(self.target)


@pydantic.type(models.ConditionGroup, all_fields=True)
class ConditionGroupType:
    pass


@pydantic.type(models.ReportColumn)
class ReportColumnType:
    id: auto
    index: auto
    report: LazyType["ReportType", __name__]
    detail: DetailType


@pydantic.type(models.Query)
class QueryType:
    select: auto
    values: List[ConditionValue]


@pydantic.type(models.Report)
class ReportType:
    id: auto
    condition_groups: auto
    root_operation: auto
    columns: auto
    owner: PydanticObjectId

    def from_pydantic(instance: models.Report, extra: Dict[str, Any] = None):
        dict = instance.dict()
        owner = dict.pop("owner")
        id = owner.ref.id
        return ReportType(owner=id, **dict)

    @strawberry.field
    async def query(self) -> Optional[QueryType]:
        loader: Report = await report_loader.load(self.id)
        transformer: SqlTransformer = await SqlTransformer.from_report(loader)
        (query, values) = await transformer.transform()
        return Query(select=query, values=values)
