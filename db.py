from gridfs import Database
from h11 import Data
from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase

class Database:
    __instance: MongoClient = None
    @staticmethod
    def instance() -> MongoDatabase:
        if Database.__instance is None:
            Database.__instance = MongoClient()
        return Database.__instance.query_builder_db
