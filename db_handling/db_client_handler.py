import pymongo

def get_db_client(db_client: pymongo.MongoClient = None) -> pymongo.MongoClient:
    return pymongo.MongoClient() if not db_client else db_client