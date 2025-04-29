from pymongo import MongoClient
from datetime import datetime
import os

def get_db():
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    db = client.get_database()
    return db

def get_collection(collection_name):
    db = get_db()
    return db[collection_name]

def search_events(search_params):
    event_collection = 'events'
    collection = get_collection(event_collection)

    # Build your base filter
    dto_filter = search_params.get("dto_date_time", {})

    # Filter only future events
    if not dto_filter:
        dto_filter["$gte"] = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        # Re-assign it back
        search_params["dto_date_time"] = dto_filter

    documents = collection.find(
        search_params,
        {"_embedding": 0}
    ).sort('dto_date_time', -1)

    document_list = list(documents)
    return document_list

def get_random_events(size):
    event_collection = 'events'
    collection = get_collection(event_collection)

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    random_docs = list(collection.aggregate(
        [
            {"$match": {"dto_date_time": {"$gte": today}}},
            {"$sample": {"size": size}},
            {"$project": {"_embedding": 0}}
        ])
    )
    return random_docs
