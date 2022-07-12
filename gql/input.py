import dataclasses
from typing import Optional

from strawberry import auto
from strawberry.experimental import pydantic

import models
from models import Entity, Property

# === Complete Inputs ===
from gql.types import ObjectId


@pydantic.input(models.User)
class UserInput:
    username: auto
    password: auto


@pydantic.input(models.Entity, all_fields=True)
class EntityInput:
    pass


@pydantic.input(models.Property)
class PropertyInput:
    database_name: auto
    display_name: auto
    type: auto
    entity: ObjectId
    refers_to: Optional[ObjectId]

    async def to_pydantic(self):
        data = dataclasses.asdict(self)
        entity_id = data.pop("entity")
        ref_id = data.pop('refers_to')
        entity = await Entity.get(entity_id)
        reference = None if ref_id is None else await Property.get(ref_id)
        return Property(refers_to=reference, entity=entity, **data)
# === Partial Inputs ===  For edit requests
