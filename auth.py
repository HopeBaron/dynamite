import json
from datetime import datetime, timedelta
from typing import List, Optional

import pyseto
from pyseto import Key

from models import Session, User, ConditionGroup, Entity




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

    def create_token(self, master_token):
        return pyseto.encode(self.private_key, payload={"data": {'master_token': str(master_token), 'used_since': datetime.utcnow()}}, serializer=json)

    def create_session(
            self,
            user: User,
            master_token: Optional[str] = None,
            database_access: List[Entity]=[],
            conditions: List[ConditionGroup] = []) -> Session:
        token = self.create_token(master_token)
        return Session.construct(
            token=str(token, 'UTF-8'),
            master_token=master_token,
            user=user,
            used_since = datetime.utcnow(),
            conditions=conditions,
            database_access=database_access
        )
    def verify_token(self, token):
        return Session.find_one(Session.token == token)

