
from beanie import PydanticObjectId


async def get_entities(cls, limit=100):
    return await cls.find_many(limit=limit).to_list()


async def get_entity(cls, id: PydanticObjectId):
    return await cls.find_one(cls.id == id)


def modelize_input(input):
    model_input = input.to_pydantic()
    return model_input.dict(exclude_unset=True)


def get_object(cls, input):
    model = modelize_input(input)
    return cls(**model)


async def create_entity(cls, input):
    obj = get_object(cls, input)
    return await obj.insert()


async def delete_entity(cls, id):
    entity = await get_entity(cls, id)
    if entity is None:
        return None
    await entity.delete()
    return entity
