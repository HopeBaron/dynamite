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



@pydantic.input(models.Condition, all_fields=True)
class ConditionInput:
    pass

@pydantic.input(models.ConditionGroup, all_fields=True)
class ConditionGroupInput:
    pass

@pydantic.input(models.Join, all_fields=True)
class JoinInput:
    pass

@pydantic.input(models.ReportColumn, all_fields=True)
class ReportColumnInput:
    pass


@pydantic.input(models.Report, all_fields=True)
class ReportInput:
    pass
