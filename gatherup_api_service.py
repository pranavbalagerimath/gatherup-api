from flask import Flask, request, jsonify
import bcrypt
import pandas as pd
from flask_cors import CORS
from database_utils import execute_sql_query, get_sql_database_connection
from datetime import datetime, timedelta
from mongo_database_utils import search_events, get_random_events
import os
import jwt
from functools import wraps
import requests
from tfidf_trainer import train_tfidf_model
from recommender import MLRecommender

app = Flask(__name__)

CORS(app)

#JWT token that is returned after login, and then is used for session management.
#For all subsequent requests, the JWT token is used to authenticate the user.

SECRET_KEY = os.getenv("SECRET_KEY", "")
TOKEN_EXPIRATION_TIME_IN_HOURS = 5

# Decorator to require token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Look for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            # Decode the token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Register User Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    # Extract user details from request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    # Optional fields
    full_name = data.get('full_name', '')
    bio = data.get('bio', '')
    location = data.get('location', '')
    preferences = data.get('preferences', [])

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    existing_user_details_query = """select username, email from users"""
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
        query = """INSERT INTO Users (username, email, password_hash, full_name, bio, location, preferences)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        execute_sql_query(query, args=(username, email, hashed_password.decode('utf-8'), full_name, bio, location, preferences))
        get_sql_database_connection().commit()
        token = jwt.encode(
            {"username": username, "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_TIME_IN_HOURS)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"message": "User registered successfully!", "results": {"token": token}}), 201
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
        token = jwt.encode(
            {"username": username, "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_TIME_IN_HOURS)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"message": "Login successful", "results": {"token": token}}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/getLandingEvents', methods=['GET'])
def get_landing_events():
    events = get_random_events(size=50)
    return jsonify({'data': events}), 200

@app.route('/searchEvents', methods=['POST'])
def search():
    query_params = request.json
    print(query_params)
    search_params = {}

    state = query_params.get('state', '')
    if state and state != '':
        search_params['venue.state'] = state

    city = query_params.get('city', '')
    if city != '':
        search_params['venue.city'] = city

    event_name = query_params.get('name', '')
    if event_name != '':
        search_params['name'] = {"$regex": event_name, "$options": "i"}

    event_date = query_params.get('date', '')
    if event_date != '':
        start_date = datetime.strptime(event_date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1)
        search_params['dto_date_time'] = {'$gte': start_date, '$lt': end_date}

    # Fix the categories parameter handling
    categories = query_params.get('categories', [])
    if categories:
        # If it's a string, use it directly
        if isinstance(categories, str):
            search_params['classifications.genre'] = categories
        # If it's a non-empty list, use $in operator to match any of the categories
        elif isinstance(categories, list) and len(categories) > 0:
            search_params['classifications.genre'] = {"$in": categories}

    print("Final search parameters:", search_params)
    events = search_events(search_params)

    return jsonify({'data': events}), 200

@app.route('/getPreferences', methods=['POST'])
def get_preferences():
    query_params = request.json

    username = query_params.get("username")

    if not username:
        return jsonify({'error': 'username missing in the request'}), 500
    query = f'''
    select preferences from users where username='{username}'
    '''
    cursor = execute_sql_query(query)
    result = cursor.fetchall()

    if not result:
        return jsonify({'error': 'User does not exist in the database'}), 500

    return jsonify({'data': result[0][0]}), 200

@app.route('/scrape_url', methods=['POST'])
def get_scrape_data():
    query_params = request.json

    url = query_params.get('url')
    headers =  {"User-Agent": "Mozilla/5.0"}
    if url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None
        return response.text
    return jsonify({'error': 'Missing URL parameter'}), 500

@app.route('/train_recommendation_model', methods=['POST'])
def train_recommender():
    try:
        train_tfidf_model()
        return jsonify({'message': 'Training completed Successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/getRecommendation', methods=['POST'])
def get_recommendation():
    query_params = request.json

    username = query_params.get('username')

    if not username:
        return jsonify({'error': 'Username must be present!'})

    query = f'''
        select preferences, location from users where username='{username}'
        '''
    cursor = execute_sql_query(query)
    result = cursor.fetchall()

    if not result:
        return jsonify({'error': 'User does not exist in the database'}), 500

    user_categories = result[0][0] if result[0][0] else ["Music", "Comedy"]
    user_cities = [result[0][1]] if result[0][1] else ["Los Angeles", "San Francisco", "New York"]

    # Initialize and get recommendations
    recommender = MLRecommender()
    results = recommender.recommend(
        preferred_categories=user_categories,
        preferred_locations=user_cities,
        top_n=20
    )

    return jsonify({'data': results}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
