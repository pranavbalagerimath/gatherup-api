from pymongo import MongoClient
import os

def search_events(search_params):
    event_collection = 'events'
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    db = client.get_database()
    collection = db[event_collection]
    documents = collection.find(
        search_params
    ).sort('date_time', 1)

    document_list = list(documents)
    return document_list
