from typing import List, Dict, Any

import strawberry
from beanie import PydanticObjectId
from strawberry import auto
from strawberry.experimental import pydantic

import models
from report import ReportBuilder

# === Scalers ===

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


# === Authentication models ===

@pydantic.type(model=models.User)
class UserType:
    username: auto
    name: auto
    permissions: List[models.Permission]

    @staticmethod
    def from_pydantic(instance: models.User, extra: Dict[str, Any] = None) -> "UserType":
        data = instance.dict()
        permissions = data.pop("permissions")
        data["permissions"] = instance.permissions.permissions
        data.pop("id")
        data.pop("password")
        return UserType(**data)


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
    columns: List[ColumnReferenceNotationScaler]


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
        return ReportBuilder(self).build()
