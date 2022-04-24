from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from gql.schema import schema

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")