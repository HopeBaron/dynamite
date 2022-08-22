from datetime import datetime
from typing import List, Optional, TypeVar, Any

import bcrypt
import pymongo
from beanie import Document, Link, PydanticObjectId
from beanie.odm.operators.find.comparison import In
from pydantic import BaseModel, validator, Field
from pymongo import IndexModel
from sql import Table
from typing_extensions import Self

from dynamite.enums import DetailExpectedType, WhereOperations, ConditionGroupOperations
from dynamite.utils import get_model, normalize, sort_by_index


class EmbeddedDocument(BaseModel):
    id: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="id")


class DatabaseModel(BaseModel):
    database_name: str
    display_name: str

    _normalize_database_name = validator('database_name', allow_reuse=True)(normalize)


class User(Document):
    username: str
    password: str

    @classmethod
    async def create_user(cls, username, password) -> Self:
        matching_user = await User.find_one(User.username == username)
        if matching_user:
            raise ValueError("This username is already taken.")
        encoded_password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(encoded_password, salt)
        user = User(username=username, password=hashed)
        await user.save()
        return user

    @staticmethod
    async def validate_credentials(username: str, password: str):
        user: User = await User.find_one(User.username == username)
        if not user:
            return None
        hashed_password = user.password.encode('utf-8')
        encoded_password = password.encode('utf-8')
        correct_password = bcrypt.checkpw(encoded_password, hashed_password)
        if correct_password:
            return user

        return None


class Detail(DatabaseModel, EmbeddedDocument):
    type: DetailExpectedType = DetailExpectedType.STRING
    refers_to: Optional[PydanticObjectId]

    @property
    def topic(self):
        return Topic.has_detail(self.id)

    async def sql(self):
        entity = await self.topic
        table = entity.sql()
        column_name = self.database_name
        return table.__getattr__(column_name)

    class Settings:
        indexes = [
            IndexModel([("entity", pymongo.ASCENDING), ("database_name", pymongo.ASCENDING)], unique=True,
                       name="entity_name_index")
        ]

    @property
    def references(self):
        return Detail.find(Detail.refers_to.id == self.id)


class Topic(DatabaseModel, Document):
    pivot: bool = False
    owner: Optional[Link[User]]
    details: List[Detail]

    @staticmethod
    def has_detail(id: PydanticObjectId):
        return Topic.find_one(In(Topic.details.id, [id]))

    def detail(self, item):
        return [value for value in self.details if value.id == item][0]

    def sql(self):
        return Table(self.database_name)

    class Settings:
        indexes = [
            IndexModel([("database_name", pymongo.ASCENDING)], unique=True, name="database_name_index")
        ]


Topic.update_forward_refs()

Detail.update_forward_refs()

T = TypeVar("T")


class Condition(EmbeddedDocument):
    operation: WhereOperations
    index: int = 0
    target: PydanticObjectId
    value: List[Any]

    async def as_detail(self):
        topic = await Topic.has_detail(self.target)
        return topic.detail(self.target)


class ConditionGroup(EmbeddedDocument):
    operation: ConditionGroupOperations
    index: int = 0
    conditions: List[Condition]

    _sort_conditions = validator('conditions', allow_reuse=True)(sort_by_index)

    async def as_details(self):
        return [await condition.as_detail() for condition in self.conditions]


class ReportColumn(DatabaseModel, EmbeddedDocument):
    index: int = 0
    detail: PydanticObjectId

    async def sql(self):
        prop = await self.fetched_detail
        return prop.sql()

    @property
    def fetched_topic(self):
        return Topic.has_detail(self.detail)

    @property
    async def fetched_detail(self):
        entity = await self.fetched_topic
        return entity.detail(self.detail)


class Session(Document):
    token: str
    context: Optional[str]
    master_token: Optional[str]
    user: Link[User]
    used_since: datetime
    topic_access: List[Link[Topic]] = []
    conditions: List[ConditionGroup] = []

    async def create_slave_session(self,
                                   context: str,
                                   database_access: List[Link[Topic]],
                                   conditions: List[ConditionGroup]):
        from auth import Auth
        return Auth().create_session(
            context,
            self.user,
            self.token,
            database_access,
            conditions
        )


class Query(BaseModel):
    select: str
    values: List[Any]


class Report(DatabaseModel, Document):
    condition_groups: List[ConditionGroup] = []
    columns: List[ReportColumn] = []
    root_operation: ConditionGroupOperations = ConditionGroupOperations.AND
    owner: Optional[Link[Session]]
    context: Optional[str]
    _sort_condition_groups = validator('condition_groups', allow_reuse=True)(sort_by_index)


ReportColumn.update_forward_refs()
