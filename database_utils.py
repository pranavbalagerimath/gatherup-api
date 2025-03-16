import os
from dotenv import load_dotenv
import mysql.connector
from bson import ObjectId
import psycopg2

load_dotenv()

conn = None
def get_sql_database_connection():
    global conn

    if conn:
        return conn

    # PostgreSQL Configuration
    conn = psycopg2.connect(
        host=os.getenv('SQL_HOST'),
        port=os.getenv('SQL_PORT'),
        user=os.getenv('SQL_USER'),
        password=os.getenv('SQL_PASSWORD'),
        dbname="gatherup"
    )

    return conn

def execute_sql_query(query, args=None):
    cursor = get_sql_database_connection().cursor()
    cursor.execute(query, args)
    return cursor

def commit():
    get_sql_database_connection().commit()