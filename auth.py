import json
from datetime import datetime, timedelta
from pprint import pprint

import pyseto
from pyseto import Key

from models import Session, User


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
    
    async def __store_token(self, token, exp,since, user):
        session = Session(token=token, user=user, exp=exp, used_since= since)
        return await session.save()
        
    async def form_token(self, user: User) -> Session:
        now = datetime.utcnow()
        delta = timedelta(days=7)
        expiration_date = now + delta
        payload = {"data": {"username": user.username, "used_since": str(now)} }
     
        token = pyseto.encode(self.private_key, payload=payload, serializer=json, exp=timedelta.total_seconds(delta))
        return await self.__store_token(token, expiration_date, now, user)
    
    async def verify_token(self, token):
        decoded = pyseto.decode(self.public_key, token, deserializer=json)
        payload = decoded.payload
        data = payload['data']
        username = data["username"]
        saved_session = await Session.find_one(Session.token == token)
        await saved_session.fetch_link(Session.user)
        return saved_session.user.username == username if saved_session else False
         
    
            