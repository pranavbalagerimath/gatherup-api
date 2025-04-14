import pytest
from gatherup_api_service import app
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime, timedelta

load_dotenv()

@pytest.fixture(scope="module")
def test_client():
    app.config["TESTING"] = True

    client = app.test_client()
    test_mongo_client = MongoClient(os.getenv("MONGO_URI"))
    db = test_mongo_client.get_database()

    # Sample test data
    test_events = [
        {
            "name": "Hamilton (NY)",
            "date_time": "2025-03-05T00:00:00Z",
            "dto_date_time": datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
            "venue": {
                "name": "Richard Rodgers Theatre",
                "city": "New York",
                "state": "NY",
                "country": "US"
            },
            "classifications":
                {"genre": "Arts & Theatre"},
        },
        {
            "name": "Phantom of the Opera",
            "date_time": "2025-03-10T00:00:00Z",
            "dto_date_time": (datetime.today() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            "venue": {
                "name": "Majestic Theatre",
                "city": "Chicago",
                "state": "IL",
                "country": "US"
            },
            "classifications": {"genre": "Musicals"},
        }
    ]

    for doc in test_events:
        # Create a new ObjectId and convert it to a string
        doc["_id"] = str(ObjectId())

    # Insert test data
    db.events.insert_many(test_events)

    yield client  # Provide test client to test functions

    # Cleanup: Remove test data after tests
    db.events.delete_many({})

@pytest.mark.parametrize("query_params, expected_count", [
    ({"state": "NY"}, 1),  # Only 1 event in NY
    ({"city": "Chicago"}, 1),  # Only 1 event in Chicago
    ({"name": "Hamilton"}, 1),  # Partial match with regex
    ({"eventDate": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")}, 1),  # Exact date match
    ({"categories": "Musicals"}, 1),  # Category filter
    ({"state": "NY", "categories": "Arts & Theatre"}, 1),  # Multiple filters
    ({"state": "CA"}, 0)  # No events in California
])
def test_search_events(test_client, query_params, expected_count):
    response = test_client.post("/searchEvents", json=query_params)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == expected_count
