from enum import Enum

import strawberry


@strawberry.enum
class PropertyType(Enum):
    NUMBER = "Number"
    STRING = "String"
    BOOLEAN = "Boolean"


@strawberry.enum
class ConditionGroupOperation(Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"


@strawberry.enum
class WhereOperation(Enum):
    EQ = "EQ"
    IN = "IN"

    BETWEEN = "BETWEEN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "lTE"
    NEQ = "NEQ"


@strawberry.enum
class ColumnJoin(Enum):
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    INNER = "INNER JOIN"

