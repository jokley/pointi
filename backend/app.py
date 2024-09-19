from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

# Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    return conn

@app.route('/')
def index():
    return jsonify({"message": "Hello from Flask on Raspberry Pi!"})

@app.route('/data')
def get_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM your_table;')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)
