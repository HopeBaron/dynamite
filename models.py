from datetime import datetime
from typing import List, Optional

import bcrypt
import pymongo
from beanie import Document, Link, PydanticObjectId, UnionDoc
from pydantic import BaseModel, validator, Field
from pymongo import IndexModel
from typing_extensions import Self

from enums import PropertyTypes, WhereOperations, ConditionGroupOperations
from utils import create_model, get_model, normalize, sort_by_index


class EmbeddedDocument(BaseModel):
    id: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")


class DatabaseModel(BaseModel):
    database_name: str
    display_name: str

    _normalize_database_name = validator('database_name', allow_reuse=True)(normalize)


class User(Document):
    username: str
    password: str

    @classmethod
    async def create_user(cls, username, password) -> Self:
        matching_users = await User.find(User.username == username).count()
        if matching_users != 0:
            raise ValueError("This username is already taken.")
        encoded_password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(encoded_password, salt)
        user = User(username=username, password=hashed)
        await user.save()
        return user

    @staticmethod
    async def validate_credentials(username: str, password: str):
        user: User = await get_model(User, username=username)
        if not user:
            return None
        hashed_password = user.password.encode('utf-8')
        encoded_password = password.encode('utf-8')
        correct_password = bcrypt.checkpw(encoded_password, hashed_password)
        if correct_password:
            return user

        return None


class Property(DatabaseModel, Document):
    type: PropertyTypes = PropertyTypes.STRING
    entity: Link["Entity"]
    refers_to: Optional[Link["Property"]]

    async def sql(self):
        entity = await self.entity.fetch()
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
        return Property.find(Property.refers_to.id == self.id)


class Entity(DatabaseModel, Document):
    pivot: bool = False
    owner: Link[User]

    def prop(self, item):
        pass

    @property
    def properties(self):
        return Property.find(Property.entity.id == self.id)

    class Settings:
        indexes = [
            IndexModel([("database_name", pymongo.ASCENDING)], unique=True, name="database_name_index")
        ]


Entity.update_forward_refs()

Property.update_forward_refs()


class Condition(EmbeddedDocument):
    operation: WhereOperations
    index: int = 0
    target: PydanticObjectId
    value: List[str]

    async def as_property(self):
        return await Property.get(self.target)


class ConditionGroup(EmbeddedDocument):
    operation: ConditionGroupOperations
    index: int = 0
    conditions: List[Condition]

    _sort_conditions = validator('conditions', allow_reuse=True)(sort_by_index)

    async def as_properties(self):
        return [await condition.as_property() for condition in self.conditions]


class ReportColumn(DatabaseModel, Document):
    index: int = 0
    report: Link["Report"]
    property: Link[Property]

    def sql(self):
        return self.property.sql()


class Session(Document):
    token: str
    master_token: Optional[str]
    user: Link[User]
    used_since: datetime
    database_access: List[Link[Entity]] = []
    conditions: List[ConditionGroup] = []

    async def create_slave_session(self,
                                   database_access: List[Link[Entity]],
                                   conditions: List[ConditionGroup]):
        from auth import Auth
        return Auth().create_session(
            self.user,
            self.token,
            database_access,
            conditions
        )


class Query(BaseModel):
    select: str
    values: List[str]


class Report(DatabaseModel, Document):
    condition_groups: List[ConditionGroup] = []
    root_operation: ConditionGroupOperations = ConditionGroupOperations.AND
    owner: Link[Session]
    _sort_condition_groups = validator('condition_groups', allow_reuse=True)(sort_by_index)

    def columns(self, fetch_links: bool = True):
        return ReportColumn.find(ReportColumn.report.id == self.id, fetch_links=fetch_links)


ReportColumn.update_forward_refs()
