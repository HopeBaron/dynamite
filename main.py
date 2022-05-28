import asgiref
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from strawberry.fastapi import GraphQLRouter
from gql.schema import schema
from models import Report, Table
from motor.motor_asyncio import AsyncIOMotorClient
async def init_database():
    # Beanie uses Motor under the hood 
    client = AsyncIOMotorClient()

    # Init beanie with the Product document class
    await init_beanie(database=client.qb_db, document_models=[Table, Report])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
graphql_app = GraphQLRouter(schema)

app = FastAPI(on_startup=[init_database])
app.include_router(graphql_app, prefix="/graphql")