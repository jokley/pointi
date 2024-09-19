from flask import Flask, jsonify, request, render_template
import psycopg2
from psycopg2.extras import execute_values
import logging
from dotenv import load_dotenv
import os

app = Flask(__name__)

def get_db_connection():
    # Fetch database connection details from environment variables
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    return conn


# Configure logging
logging.basicConfig(level=logging.INFO)

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

@app.route('/api/new_race', methods=['POST'])
def new_race():
    try:
        data = request.json

        app.logger.info(data)

        raceinfo = data['raceinfo']
        starters = data['starters']
        start_classes = data['startclasses']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert race information
        cursor.execute("""
            INSERT INTO races (federation, sector, discipline, codex, race_date, nr_of_runs)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING race_id
        """, (raceinfo['federation'], raceinfo['sector'], raceinfo['discipline'], raceinfo['codex'], raceinfo['racedate'], raceinfo['nr_of_runs']))
        race_id = cursor.fetchone()[0]

        # Insert start classes
        start_class_values = [
            (race_id, sc['start_class_nr'], sc['description'], sc['desc_short'], sc['sex'], sc['year_from'], sc['year_to'], sc['nr_of_runs'], sc['nr_of_runs_eval'], sc['entry_fee'], sc['additional_fee'], sc['drawing_class'], sc['starttime'], sc['interval'], sc['distance'])
            for sc in start_classes
        ]
        execute_values(cursor, """
            INSERT INTO start_classes (race_id, start_class_nr, description, desc_short, sex, year_from, year_to, nr_of_runs, nr_of_runs_eval, entry_fee, additional_fee, drawing_class, start_time, interval, distance)
            VALUES %s
            ON CONFLICT (race_id, start_class_nr) DO NOTHING
        """, start_class_values)

        # Insert athletes
        athlete_values = [
            (ath['firstname'], ath['surname'], ath['birth_year'], ath['birth_month'], ath['birth_day'], ath['sex'], ath['club_code'], ath['clubname'])
            for ath in starters
        ]
        execute_values(cursor, """
            INSERT INTO athletes (firstname, surname, birth_year, birth_month, birth_day, sex, club_code, clubname)
            VALUES %s
            ON CONFLICT (firstname, surname, birth_year, birth_month, birth_day) DO NOTHING
        """, athlete_values)

        # Insert race results
        race_result_values = [
            (race_id, ath['bib'], ath['start_class_nr'], ath['start_points'], ath['seed'], ath['entry_fee'], ath['additional_fee'], ath['status'], ath['status_run'], ath['rank'], ath['time_hour'], ath['time_min'], ath['time_sec'], ath['time_thous'], ath['dis_gate'], ath['race_points'], ath['intl_code'])
            for ath in starters
        ]
        execute_values(cursor, """
            INSERT INTO race_results (race_id, bib, start_class_nr, start_points, seed, entry_fee, additional_fee, status, status_run, rank, time_hour, time_min, time_sec, time_thous, dis_gate, race_points, intl_code)
            VALUES %s
            ON CONFLICT (race_id, bib, start_class_nr) DO NOTHING
        """, race_result_values)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success"})

    except (Exception, psycopg2.DatabaseError) as error:
        app.logger.error(f"Error: {error}")
        return jsonify({"status": "error", "message": str(error)}), 500


# if __name__ == '__main__':
#     app.run(debug=True)
