from pymongo import MongoClient

DATABASE_NAME = 'event_data'
EVENT_COLLECTION = 'events'
client = MongoClient("mongodb://localhost:27017/")
db = client[DATABASE_NAME]

def search_events(search_params):
    collection = db[EVENT_COLLECTION]
    documents = collection.find(
        search_params
    ).sort('date_time', 1)

    document_list = list(documents)
    return document_list
