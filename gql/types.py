from typing import List, Optional, Dict, Any

import strawberry
from beanie import PydanticObjectId
from strawberry import auto, LazyType
from strawberry.experimental import pydantic

from models import Query
import models
from gql.dataloaders import entity_loader, report_loader, property_loader

# === Scalers ===
from transformer import SqlTransformer

ObjectId = strawberry.scalar(
    PydanticObjectId,
    serialize=lambda v: str(v),
    parse_value=lambda v: PydanticObjectId(v),
    description="MongoDB ObjectId"
)


# === Authentication models ===

@pydantic.type(model=models.User)
class UserType:
    username: auto


@strawberry.type
class LoginSuccess:
    user: UserType
    token: str


@strawberry.type
class LoginError:
    message: str


LoginResult = strawberry.union("LoginResult", (LoginSuccess, LoginError))


# === Domain models ===

@pydantic.type(models.Property)
class PropertyType:
    id: ObjectId
    type: auto
    display_name: auto
    database_name: auto

    @strawberry.field
    async def references(self) -> List["PropertyType"]:
        prop = await property_loader.load(self.id)
        return await prop.references.to_list()

    @strawberry.field
    async def refers_to(self) -> Optional["PropertyType"]:
        prop = await property_loader.load(self.id)
        return prop.refers_to


@pydantic.type(models.Entity)
class EntityType:
    id: ObjectId
    properties: List["PropertyType"]
    pivot: auto
    display_name: auto
    database_name: auto
    owner: UserType


@pydantic.type(models.Condition)
class ConditionType:
    id: auto
    operation: auto
    index: auto
    value: auto
    target: ObjectId

    async def target_object(self):
        return await property_loader.load(self.target)


@pydantic.type(models.ConditionGroup, all_fields=True)
class ConditionGroupType:
    pass


@pydantic.type(models.ReportColumn)
class ReportColumnType:
    id: auto
    index: auto
    report: LazyType["ReportType", __name__]
    prop: PropertyType


@pydantic.type(models.Query, all_fields=True)
class QueryType:
    pass


@pydantic.type(models.Report)
class ReportType:
    id: auto
    condition_groups: auto
    root_operation: auto
    owner: PydanticObjectId

    def from_pydantic(instance: models.Report, extra: Dict[str, Any] = None):
        dict = instance.dict()
        owner = dict.pop("owner")
        id = owner.ref.id
        return ReportType(owner=id, **dict)
    @strawberry.field
    async def columns(self) -> List["ReportColumnType"]:
        loader = await report_loader.load(self.id)
        return loader.columns

    @strawberry.field
    async def query(self) -> Optional[QueryType]:
        loader = await report_loader.load(self.id)
        transformer = await SqlTransformer.from_report(loader)
        (query, values) = await transformer.transform()
        return Query(select=query, values=values)
