from enum import Enum

import strawberry


@strawberry.enum
class DetailType(Enum):
    NUMBER = "Number"
    STRING = "String"
    BOOLEAN = "Boolean"

@strawberry.enum
class ConditionGroupOperations(Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"


@strawberry.enum
class WhereOperations(Enum):
    EQ = "EQ"
    IN = "IN"

    BETWEEN = "BETWEEN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "lTE"
    NEQ = "NEQ"


@strawberry.enum
class ColumnJoins(Enum):
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    INNER = "INNER JOIN"
