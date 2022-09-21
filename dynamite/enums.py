from enum import Enum
from typing import Dict, List

import strawberry


@strawberry.enum
class DetailExpectedType(Enum):
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


operations: Dict[DetailExpectedType, List[WhereOperations]] = {
    DetailExpectedType.NUMBER: [
        WhereOperations.EQ,
        WhereOperations.GT,
        WhereOperations.GTE,
        WhereOperations.LTE,
        WhereOperations.LT,
        WhereOperations.BETWEEN,
        WhereOperations.NEQ,
        WhereOperations.IN
    ],
    DetailExpectedType.BOOLEAN: [
        WhereOperations.EQ,
        WhereOperations.NEQ
    ],
    DetailExpectedType.STRING: [
        WhereOperations.EQ,
        WhereOperations.NEQ,
        WhereOperations.IN
    ]
}
