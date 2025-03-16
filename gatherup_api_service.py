from flask import Flask, request, jsonify
import bcrypt
import pandas as pd
from database_utils import execute_sql_query, get_sql_database_connection
from datetime import datetime, timedelta
from mongo_database_utils import search_events
import os
from pymongo import MongoClient

app = Flask(__name__)

# Use environment variable to determine which database to connect to
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/event_db")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.get_database()

# Register User Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    # Extract user details from request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name', '')
    bio = data.get('bio', '')
    location = data.get('location', '')

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    existing_user_details_query = """ select username, email from users"""
    cursor = execute_sql_query(existing_user_details_query)
    results = cursor.fetchall()
    user_df = pd.DataFrame(results, columns=["username", "email"])
    if username in user_df['username'].values:
        return jsonify({"error": "username already exist!"}), 400

    if email in user_df['email'].values:
        return jsonify({"error": "An account already exist for this email!"}), 400

    if full_name == '':
        return jsonify({"error": "Please enter your full name"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        query = """INSERT INTO Users (username, email, password_hash, full_name, bio, location)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        execute_sql_query(query, args=(username, email, hashed_password, full_name, bio, location))
        get_sql_database_connection().commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as err:
        return jsonify({"error": str(err)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Fetch user details from the database
    query = "SELECT password_hash FROM Users WHERE username = %s"
    cursor = execute_sql_query(query, (username,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "Invalid username or password"}), 401

    stored_hash = result[0]

    # Verify the password
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/searchEvents', methods=['GET'])
def search():
    query_params = request.args
    search_params = {}

    state = query_params.get('state', '')
    if state != '':
        search_params['venue.state'] = state

    city = query_params.get('city', '')
    if city != '':
        search_params['venue.city'] = city

    event_name = query_params.get('name', '')
    if event_name != '':
        search_params['name'] = {"$regex": event_name, "$options": "i"}

    event_date = query_params.get('eventDate', '')
    if event_date != '':
        start_date = datetime.strptime(event_date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1)
        search_params['date_time'] = {'$gte': start_date.isoformat(), '$lt': end_date.isoformat()}

    category = query_params.get('category', '')
    if category != '':
        search_params['category'] = category

    events = search_events(search_params)

    return jsonify({'data': events}), 200


if __name__ == '__main__':
    app.run(debug=True)
