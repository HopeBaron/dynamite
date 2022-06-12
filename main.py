from beanie import init_beanie
from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

import models
from auth import Auth
from gql.schema import schema
from models import Report, Session, Table, User


async def init_database():
    client = AsyncIOMotorClient()

    await init_beanie(database=client.qb_db, document_models=[Table, Report, User, Session])


async def get_user(request: Request) -> models.User | None:
    print("Request", request)
    token = request.headers['Authorization']
    return await Auth().verify_token(token)


async def custom_context(user=Depends(get_user)):
    return {
        "user": user
    }

graphql_app = GraphQLRouter(schema, context_getter=custom_context)

app = FastAPI(on_startup=[init_database])
app.include_router(graphql_app, prefix="/graphql")
