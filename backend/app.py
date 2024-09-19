from flask import Flask, jsonify, request, render_template
import psycopg2

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="skiers",
        user="yourusername",
        password="yourpassword"
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# API Route to get top 10 ranked athletes
@app.route('/api/top10', methods=['GET'])
def get_top_10():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT a.firstname, a.surname, r.rank, r.time_sec 
                   FROM RaceResults r
                   JOIN Athletes a ON r.athlete_id = a.athlete_id
                   ORDER BY r.rank ASC LIMIT 10;''')
    results = cur.fetchall()
    cur.close()
    conn.close()

    # Convert results to a dictionary
    top_10 = [{"firstname": row[0], "surname": row[1], "rank": row[2], "time_sec": row[3]} for row in results]
    return jsonify(top_10)

# API Route to submit new race data
@app.route('/api/new_race', methods=['POST'])
def new_race():
    data = request.json  # Assuming race data is sent as JSON from the frontend
    # Insert race data into database...
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
