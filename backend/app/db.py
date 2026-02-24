import os
import psycopg2

def get_connection():
	return psycopg2.connect(
		host=os.getenv("DB_HOST"),
		port=os.getenv("DB_PORT"),
		dbname=os.getenv("DB_NAME"),
		user=os.getenv("DB_USER"),
		password=os.getenv("DB_PASS"),
	)

def fetch_all(query, params=None):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(query, params or ())
	rows = cur.fetchall()
	cur.close()
	conn.close()
	return rows

def execute(query, params=None):
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(query, params or ())
	conn.commit()
	cur.close()
	conn.close()
