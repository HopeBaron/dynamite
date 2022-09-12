from typing import List

from beanie import Document
from beanie.odm.operators.find.comparison import In
from strawberry.dataloader import DataLoader

from dynamite.models import Topic, Detail, Report


async def load(cls: Document, keys):
    return await cls.find_many(In(cls.id, keys), fetch_links=True).to_list()


async def load_entity(keys) -> List[Topic]:
    return await load(Topic, keys)


async def load_detail(keys) -> List[Detail]:
    async def find_detail(key):
        topic = await Topic.has_detail(key)
        return await topic.detail(key)
    return [await find_detail(key) for key in keys]


async def load_report(keys) -> List[Report]:
    return await load(Report, keys)


detail_loader = DataLoader(load_fn=load_detail)
entity_loader = DataLoader(load_fn=load_entity)
report_loader = DataLoader(load_fn=load_report)
