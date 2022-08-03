import json
from datetime import datetime, timedelta
from typing import List

import pyseto
from pyseto import Key

from models import Session, User, ConditionGroup, Entity


async def store_token(token, since, user, database_access: List[Entity] = [], conditions: List[ConditionGroup] = []):
    session = Session(token=token, user=user, used_since=since, database_access=database_access, conditions=conditions)
    return await session.save()


class Auth:
    _instance = None

    def __init__(self) -> None:
        with open("./env/private_key.pem") as key_file:
            self.private_key = Key.new(4, "public", key_file.read())

        with open("./env/public_key.pem") as key_file:
            self.public_key = Key.new(4, "public", key_file.read())

    def __new__(cls):
        if cls._instance is not None:
            return cls._instance
        cls._instance = super(Auth, cls).__new__(cls)
        return cls._instance

    async def create_token(self,
                           user: User,
                           conditions: List[ConditionGroup],
                           database_access: List[Entity]) -> Session:
        now = datetime.utcnow()
        payload = {"data": {"username": user.username, "used_since": str(now)}}

        token = pyseto.encode(self.private_key, payload=payload, serializer=json)
        return await store_token(token, now, user)

    async def verify_token(self, token):
        decoded = pyseto.decode(self.public_key, token, deserializer=json)
        payload = decoded.payload
        data = payload['data']
        username = data["username"]
        saved_session: Session = await Session.find_one(Session.token == token)
        if not saved_session:
            return None

        await saved_session.fetch_link(Session.user)
        return saved_session.user
