from typing import List, Optional

import strawberry
from beanie import PydanticObjectId, Link
from strawberry import auto
from strawberry.experimental import pydantic

import models
from gql.dataloaders import property_loader, entity_loader
from models import Property, Entity

# === Scalers ===

ObjectId = strawberry.scalar(
    PydanticObjectId,
    serialize=lambda v: str(v),
    parse_value=lambda v: PydanticObjectId(v),
    description="MongoDB ObjectId"
)


# === Authentication models ===

@pydantic.type(model=models.User)
class UserType:
    username: auto


@strawberry.type
class LoginSuccess:
    user: UserType
    token: str


@strawberry.type
class LoginError:
    message: str


LoginResult = strawberry.union("LoginResult", (LoginSuccess, LoginError))


# === Domain models ===

@pydantic.type(models.Entity)
class EntityType:
    id: ObjectId
    pivot: auto
    display_name: auto
    database_name: auto

    @strawberry.field
    async def properties(self) -> List["PropertyType"]:
        entity = await entity_loader.load(self.id)
        return await entity.properties.to_list()


@pydantic.type(models.Property)
class PropertyType:
    id: ObjectId
    type: auto
    display_name: auto
    database_name: auto

    @strawberry.field
    async def entity(self) -> EntityType:
        property = await property_loader.load(self.id)
        return await entity_loader.load(property.entity.ref.id)

    @strawberry.field
    async def refers_to(self) -> Optional["PropertyType"]:
        property = await property_loader.load(self.id)
        ref_to = property.refers_to
        ref_id = ref_to.ref.id if ref_to  else None
        if not ref_id:
            return None
        await property_loader.load(ref_id)
        return property

    @strawberry.field
    async def references(self) -> List["PropertyType"]:
        prop = await property_loader.load(self.id)
        return await prop.references.to_list()
