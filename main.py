from beanie import init_beanie
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from gql.schema import schema
from models import Report, Table, User
from motor.motor_asyncio import AsyncIOMotorClient


async def init_database():
    client = AsyncIOMotorClient()

    await init_beanie(database=client.qb_db, document_models=[Table, Report, User])


graphql_app = GraphQLRouter(schema)

app = FastAPI(on_startup=[init_database])
app.include_router(graphql_app, prefix="/graphql")
