import pytest
from datetime import datetime, timedelta
from flask import Flask
from gatherup_api_service import app  # Import Flask app and search function
from mongo_database_utils import search_events
from pymongo import MongoClient
import os

# Test database setup
TEST_DB_NAME = "test_event_db"
TEST_MONGO_URI = f"mongodb://localhost:27017/{TEST_DB_NAME}"


@pytest.fixture(scope="module")
def test_client():
    app.config["TESTING"] = True


    os.environ["MONGO_URI"] = TEST_MONGO_URI  # Ensure Flask connects to test DB
    client = app.test_client()
    test_mongo_client = MongoClient(TEST_MONGO_URI)
    db = test_mongo_client.get_database()

    # Sample test data
    test_events = [
        {
            "name": "Hamilton (NY)",
            "date_time": "2025-03-05T00:00:00Z",
            "venue": {
                "name": "Richard Rodgers Theatre",
                "city": "New York",
                "state": "NY",
                "country": "US"
            },
            "category": "Arts & Theatre",
        },
        {
            "name": "Phantom of the Opera",
            "date_time": "2025-03-10T00:00:00Z",
            "venue": {
                "name": "Majestic Theatre",
                "city": "Chicago",
                "state": "IL",
                "country": "US"
            },
            "category": "Musicals",
        }
    ]

    # Insert test data
    db.events.insert_many(test_events)

    yield client  # Provide test client to test functions

    # Cleanup: Remove test data after tests
    db.events.delete_many({})
    del os.environ["MONGO_URI"]

@pytest.mark.parametrize("query_params, expected_count", [
    ({"state": "NY"}, 1),  # Only 1 event in NY
    ({"city": "Chicago"}, 1),  # Only 1 event in Chicago
    ({"name": "Hamilton"}, 1),  # Partial match with regex
    ({"eventDate": "2025-03-05"}, 1),  # Exact date match
    ({"category": "Musicals"}, 1),  # Category filter
    ({"state": "NY", "category": "Arts & Theatre"}, 1),  # Multiple filters
    ({"state": "CA"}, 0)  # No events in California
])
def test_search_events(test_client, query_params, expected_count):
    response = test_client.get("/searchEvents", query_string=query_params)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == expected_count
