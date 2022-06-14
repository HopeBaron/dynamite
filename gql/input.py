import dataclasses
from typing import List

from strawberry import auto
from strawberry.experimental import pydantic

import models
from gql.types import ColumnReferenceNotationScaler


# === Complete Inputs ===

@pydantic.input(models.User)
class UserInput:
    username: auto
    name: auto
    password: auto
    permissions: List[models.Permission]

    def to_pydantic(self):
        data = dataclasses.asdict(self)
        permissions_set = data.pop("permissions")
        permissions = models.Permissions(permission_bits=permissions_set)
        return models.User(permissions=permissions, **data)


@pydantic.input(models.TableColumn, all_fields=True)
class TableColumnInput:
    pass


@pydantic.input(models.Table, fields=['ref_name', 'name', 'columns'])
class TableInput:
    pass


@pydantic.input(models.ColumnReferenceNotation, all_fields=True)
class ColumnReferenceNotationInput:
    pass


@pydantic.input(models.Condition)
class ConditionInput:
    operation: auto
    index: auto
    target: ColumnReferenceNotationScaler
    value: auto


@pydantic.input(models.ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass


@pydantic.input(models.TableJoin)
class JoinInput:
    type: auto
    columns: List[ColumnReferenceNotationScaler]


@pydantic.input(models.ReportColumn)
class ReportColumnInput:
    index: auto
    ref_name: auto
    name: auto
    value: ColumnReferenceNotationScaler


@pydantic.input(models.Report, all_fields=True)
class ReportInput:
    pass

# === Partial Inputs ===  For edit requests
