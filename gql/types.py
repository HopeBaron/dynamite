from typing import List, Optional

import strawberry
from beanie import PydanticObjectId, Link
from strawberry import auto, LazyType
from strawberry.experimental import pydantic

import models

# === Scalers ===

ObjectIdScalar = strawberry.scalar(
    PydanticObjectId,
    serialize=lambda v: str(v),
    parse_value=lambda v: PydanticObjectId(v),
    description="MongoDB ObjectId"
)
PropertyReferenceScaler = strawberry.scalar(
    Link[models.Property],
    serialize=lambda v: str(v),
    parse_value=lambda v: models.property_reference(v),
    description="String representation of column reference 'table.column'"
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


@pydantic.type(model=models.TableJoin)
class JoinType:
    type: auto
    columns: List[PropertyReferenceScaler]


@pydantic.type(model=models.Property)
class PropertyType:
    database_name: auto
    display_name: auto
    type: auto
    entity: str
    refers_to: Optional[PropertyReferenceScaler]


@pydantic.type(model=models.Entity, all_fields=True)
class EntityType:
    pass


@pydantic.type(model=models.Condition)
class ConditionType:
    operation: auto
    index: auto
    target: PropertyReferenceScaler
    value: auto


@pydantic.type(models.ConditionGroup)
class ConditionGroupType:
    operation: auto
    index: auto
    conditions: auto
    # condition_groups: "Optional[List[ConditionGroupType]]"


@pydantic.type(model=models.ReportColumn)
class ReportColumnType:
    index: auto
    database_name: auto
    display_name: auto
    value: PropertyReferenceScaler


@pydantic.type(model=models.Report, all_fields=True)
class ReportType:
    @strawberry.field
    def query(self) -> str:
        return self.sql()
