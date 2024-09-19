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

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

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
    try:
        data = request.json  # Assuming race data is sent as JSON from the frontend

        app.logger.info(data)

        raceinfo = data['raceinfo']  # Race information
        starters = data['starters']  # Athletes / Starters list
        runs = data['runs']  # Race runs

        # Step 1: Insert race info into races table
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO races (federation, sector, discipline, codex, race_date, nr_of_runs)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING race_id
        """, (raceinfo['federation'], raceinfo['sector'], raceinfo['discipline'], raceinfo['codex'], raceinfo['racedate'], raceinfo['nr_of_runs']))
        race_id = cursor.fetchone()[0]

        # Step 2: Insert athlete data into athletes table
        athlete_values = [(ath['firstname'], ath['surname'], ath['birth_year'], ath['sex'], ath['clubname']) for ath in starters]
        execute_values(cursor, """
            INSERT INTO athletes (firstname, surname, birth_year, sex, club)
            VALUES %s ON CONFLICT (firstname, surname) DO NOTHING
        """, athlete_values)

        # Step 3: Insert race results into race_results table
        race_result_values = [(race_id, ath['bib'], ath['rank'], ath['time_min'], ath['time_sec'], ath['time_thous']) for ath in starters]
        execute_values(cursor, """
            INSERT INTO race_results (race_id, bib, rank, time_min, time_sec, time_thous)
            VALUES %s
        """, race_result_values)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
