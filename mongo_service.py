from pymongo import MongoClient
from bson.objectid import ObjectId
from ..utils.config import Config

class MongoService:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
    
    def find_one(self, collection, query):
        return self.db[collection].find_one(query)
    
    def insert_one(self, collection, data):
        return self.db[collection].insert_one(data)
    
    def update_one(self, collection, filter, update):
        return self.db[collection].update_one(filter, update)
    
    def find(self, collection, query, projection=None, limit=10, sort_field=None, sort_direction=-1):
        cursor = self.db[collection].find(query, projection)
        if sort_field:
            cursor = cursor.sort(sort_field, sort_direction)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    # Outros métodos CRUD conforme necessário
