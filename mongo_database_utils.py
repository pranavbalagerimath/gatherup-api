from pymongo import MongoClient
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
    documents = collection.find(
        search_params
    ).sort('date_time', 1)

    document_list = list(documents)
    return document_list

def get_random_events(size):
    event_collection = 'events'
    collection = get_collection(event_collection)
    random_docs = list(collection.aggregate(
        [{"$sample": {"size": size}},
          {"$project": {"_embedding": 0}}
        ])
    )
    return random_docs
