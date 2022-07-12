from typing import List

from beanie.odm.operators.find.comparison import In
from strawberry.dataloader import DataLoader

from models import Entity, Property


async def load_entity(keys) -> List[Entity]:
    return await Entity.find_many(In(Entity.id, keys)).to_list()


async def load_property(keys) -> List[Property]:
    return await Property.find_many(In(Property.id, keys)).to_list()


property_loader = DataLoader(load_fn=load_property)
entity_loader = DataLoader(load_fn=load_entity)
