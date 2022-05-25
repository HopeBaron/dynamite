from gql.types import ColumnReferenceNotationScaler
from typing import List
from strawberry.experimental import pydantic
from strawberry import auto
import models


@pydantic.input(models.TableColumn, all_fields=True)
class TableColumnInput:
    pass


@pydantic.input(models.Table, all_fields=True)
class TableInput:
    pass


@pydantic.input(models.ColumnReferenceNotation, all_fields=True)
class ColumnReferenceNotationInput:
    pass
@pydantic.input(models.Condition)
class ConditionInput:
    operation: auto
    sequence: auto
    target: ColumnReferenceNotationScaler
    value: auto 

@pydantic.input(models.ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass

@pydantic.input(models.Join)
class JoinInput:
    type: auto
    columns: List[List[ColumnReferenceNotationScaler]]

@pydantic.input(models.ReportColumn)
class ReportColumnInput:
   index: auto
   ref_name: auto
   name: auto
   value: ColumnReferenceNotationScaler 


@pydantic.input(models.Report, all_fields=True)
class ReportInput:
    pass
