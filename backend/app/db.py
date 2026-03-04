import os # module for communication with operating system
import psycopg2 # driver for interaction with PostgreSQL database

'''
1) Establish connection to the database
2) Take environmental variables from .env file located on the server and use 
these values as credentials
3) Wrap the connection parameters into GET_CONNECTION function for reiteration
'''
def get_connection():
	return psycopg2.connect(
		host=os.getenv("DB_HOST"),
		port=os.getenv("DB_PORT"),
		dbname=os.getenv("DB_NAME"),
		user=os.getenv("DB_USER"),
		password=os.getenv("DB_PASS"),
	)

# Read data from the database and return values as an outcome
# Added 'finally' section to avoid uncatched errors or wrong queries
def fetch_all(query, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

# Execute write-query and apply changes
def execute(query, params=None):
	with get_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query, params or ())
			conn.commit()