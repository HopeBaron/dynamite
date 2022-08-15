from typing import List

from beanie import Document
from beanie.odm.operators.find.comparison import In
from strawberry.dataloader import DataLoader

from models import Entity, Property, Report


async def load(cls: Document, keys):
    return await cls.find_many(In(cls.id, keys), fetch_links=True).to_list()


async def load_entity(keys) -> List[Entity]:
    return await load(Entity, keys)


async def load_property(keys) -> List[Property]:
    return await load(Property, keys)


async def load_report(keys) -> List[Report]:
    return await load(Report, keys)


property_loader = DataLoader(load_fn=load_property)
entity_loader = DataLoader(load_fn=load_entity)
report_loader = DataLoader(load_fn=load_report)
