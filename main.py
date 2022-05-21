import asgiref
from beanie import init_beanie
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from gql.schema import schema
from models import Report, Table
import motor
async def init_database():
    # Beanie uses Motor under the hood 
    client = motor.motor_asyncio.AsyncIOMotorClient()

    # Init beanie with the Product document class
    await init_beanie(database=client.db_name, document_models=[Table, Report])


graphql_app = GraphQLRouter(schema)

app = FastAPI(on_startup=[init_database])
app.include_router(graphql_app, prefix="/graphql")