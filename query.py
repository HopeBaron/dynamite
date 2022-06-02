from sqlalchemy import text

from models import *


class QueryBuilder:
    __limits = {
        WhereOperation.BETWEEN: 2,
        WhereOperation.EQ: 0,
        WhereOperation.GT: 1,
        WhereOperation.LT: 1,
        WhereOperation.GTE: 1,
        WhereOperation.LTE: 1,
    }

    async def condition(self, condition: Condition):
        target = condition.target
        values = condition.value
        op_enum = condition.operation
        op = op_enum.value
        limit = self.__limits[op_enum]
        actual = len(values)
        if limit != 0 and actual != limit:
            outside_limit_bounderies_message = \
            f"{limit} arguments expected for {op_enum} operation on column {target} recieved {actual}"
            raise ValueError(outside_limit_bounderies_message)
        column = await target.get_column()
        typed_values = self.type_args(column.type,values)
        return f'{target} {op} ({self.__join(typed_values)})'
    
    def type_args(self, type: ColumnType, values):
        if type is ColumnType.NUMBER:
            return [f'{float(value)}' for value in values]
        if type is ColumnType.BOOLEAN:
            return [str(value.to_lower() == 'true') for value in values]
        return [f'"{value}"' for value in values]

    async def condition_list(self, conditions: List[Condition]):
        return set([await self.condition(condition) for condition in conditions])

    async def condition_group(self, conditions_group: ConditionGroup):
        result = await self.condition_list(conditions_group.conditions)
        conditions = set(result)
        # self.condition_group_list(conditions_group.condition_groups)
        groups = []
        return f' {conditions_group.operation.value} '.join(list(conditions) + groups)

    async def condition_group_list(self, conditions_groups: List[ConditionGroup]):
        return [await self.condition_group(conditions_group) for conditions_group in conditions_groups]

    def join(self, join: Join):
        def link(notations: List[ColumnReferenceNotation]):
            tables = set(notation.table for notation in notations)
            join_cols = self.__join([str(n) for n in notations], "=")
            join_tables = self.__join(tables)
            return f"{join.type.value} {join_tables} ON {join_cols}"
        return self.__join([link(columns) for columns in join.columns], " ")

    def joins(self, joins):
        return self.__join([self.join(j) for j in joins], " ")

    async def build(self, report: Report):
        columns = []
        tables = set()

        for column in report.columns:
            notation = column.value
            await notation.get_column()
            columns.append(str(notation))
            tables.add(notation.table)
        where_statements = await self.condition_group_list(report.condition_groups)
        joined_columns = self.gen_statement(columns, "SELECT")
        joined_tables = self.gen_statement(tables, "FROM")
        where_statement = self.gen_statement(where_statements, "WHERE")
        joins_statement = self.joins(report.joins)
        select_statement = f'''{joined_columns} {joined_tables} {where_statement} {joins_statement}'''
        return text(select_statement.strip())

    def gen_statement(self, data, keyword: str, joiner: str = ','):
        if len(data) == 0:
            return ""
        result = self.__join(data, joiner)
        return f'{keyword} {result}'

    @classmethod
    def __join(self, iterable, join_value=','):
        return join_value.join(iterable)

    def normalize_relation(self, dot_notation: str):
        return ColumnReferenceNotation.ref(dot_notation)
