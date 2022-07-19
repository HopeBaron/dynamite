from typing import List, Optional

import strawberry
from beanie import PydanticObjectId
from strawberry import auto, LazyType
from strawberry.experimental import pydantic

import models
from gql.dataloaders import property_loader, entity_loader, report_loader

# === Scalers ===

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

@pydantic.type(models.Entity)
class EntityType:
    id: ObjectId
    pivot: auto
    display_name: auto
    database_name: auto
    properties: List["PropertyType"]

    @strawberry.field
    async def properties(self) -> List["PropertyType"]:
        entity = await entity_loader.load(self.id)
        return await entity.properties.to_list()


@pydantic.type(models.Property)
class PropertyType:
    id: ObjectId
    type: auto
    display_name: auto
    database_name: auto
    entity: EntityType

    @strawberry.field
    async def references(self) -> List["PropertyType"]:
        prop = await property_loader.load(self.id)
        return await prop.references.to_list()

    @strawberry.field
    async def refers_to(self) -> Optional["PropertyType"]:
        prop = await property_loader.load(self.id)
        return prop.refers_to


@pydantic.type(models.Condition)
class ConditionType:
    id: auto
    operation: auto
    index: auto
    value: auto
    target: PropertyType


@pydantic.type(models.ConditionGroup, all_fields=True)
class ConditionGroupType:
    pass


@pydantic.type(models.TableJoin)
class TableJoinType:
    id: auto
    type: auto
    columns: List[PropertyType]


@pydantic.type(models.ReportColumn)
class ReportColumnType:
    id: auto
    index: auto
    report: LazyType["ReportType", __name__]
    property: PropertyType


@pydantic.type(models.Report, all_fields=True)
class ReportType:
    @strawberry.field
    async def columns(self) -> List["ReportColumnType"]:
        loader = await report_loader.load(self.id)
        return await loader.columns().to_list()

    @strawberry.field
    async def query(self) -> str:
        loader = await report_loader.load(self.id)
        return await loader.sql()
