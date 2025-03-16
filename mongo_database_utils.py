from pymongo import MongoClient
import os

DATABASE_NAME = 'event_data'
EVENT_COLLECTION = 'events'
MONGO_URI = os.getenv("MONGO_URI", f"mongodb://localhost:27017/{DATABASE_NAME}")
client = MongoClient(MONGO_URI)
db = client.get_database()

def search_events(search_params):
    collection = db[EVENT_COLLECTION]
    documents = collection.find(
        search_params
    ).sort('date_time', 1)

    document_list = list(documents)
    return document_list
