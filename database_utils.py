import os
from dotenv import load_dotenv
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
    try:
        conn = get_sql_database_connection()
        cursor = conn.cursor()
        print(f"Executing query: {query}")
        if args:
            print(f"With arguments: {args}")
        cursor.execute(query, args)
        return cursor
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise


def commit():
    get_sql_database_connection().commit()