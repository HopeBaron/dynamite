from beanie import init_beanie
from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter

from auth import Auth
from gql.schema import schema
from models import *


async def init_database():
    client = AsyncIOMotorClient("database")

    await init_beanie(database=client.qb_db, document_models=[Topic, Report, User, Session])


async def get_session(request: Request) -> Session | None:
    token = request.headers.get('Authorization', None)
    if token is None:
        return None
    return await Auth().verify_token(token)


async def custom_context(session=Depends(get_session)):
    return {
        "session": session
    }


graphql_app = GraphQLRouter(schema, context_getter=custom_context)

app = FastAPI(on_startup=[init_database])
app.include_router(graphql_app, prefix="/graphql")
