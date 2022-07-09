import dataclasses
from typing import List, Optional

from beanie import PydanticObjectId
from strawberry import auto
from strawberry.experimental import pydantic

import models
from enums import PropertyTypes
from gql.types import PropertyReferenceScaler


# === Complete Inputs ===

@pydantic.input(models.User)
class UserInput:
    username: auto
    password: auto


@pydantic.input(models.Property)
class PropertyInput:
    type: PropertyTypes
    display_name: auto
    database_name: auto
    reference: Optional[PropertyReferenceScaler]


@pydantic.input(models.Entity, all_fields=True)
class EntityInput:
    pass


@pydantic.input(models.Property)
class PropertyInput:
    database_name: auto
    display_name: auto
    type: auto
    entity: str
    refers_to: Optional[PropertyReferenceScaler]


@pydantic.input(models.Condition)
class ConditionInput:
    operation: auto
    index: auto
    target: PropertyReferenceScaler
    value: auto


@pydantic.input(models.ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass


@pydantic.input(models.TableJoin)
class JoinInput:
    type: auto
    columns: List[PropertyReferenceScaler]


@pydantic.input(models.ReportColumn)
class ReportColumnInput:
    index: auto
    database_name: auto
    display_name: auto
    value: PropertyReferenceScaler


@pydantic.input(models.Report, all_fields=True)
class ReportInput:
    pass

# === Partial Inputs ===  For edit requests
