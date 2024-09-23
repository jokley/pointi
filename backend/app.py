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

@app.route('/api/top_skiers', methods=['GET'])
def get_top_skiers():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to get the top 10 skiers based on rank or race time (adjust as necessary)
    cursor.execute("""
            SELECT a.firstname, a.surname, rr.rank, rr.time_min, rr.time_sec, rr.time_thous
            FROM race_results rr
            JOIN athletes a ON rr.athlete_id = a.athlete_id
            WHERE rr.status = 'QLF'
            ORDER BY rr.time_min ASC, rr.time_sec ASC, rr.time_thous ASC
            LIMIT 10
    """)
    top_skiers = cursor.fetchall()
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Return the results as JSON
    return jsonify(top_skiers)


@app.route('/api/new_race', methods=['POST'])
def new_race():
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert race info into races table
    cursor.execute("""
        INSERT INTO races (federation, sector, discipline, codex, race_date, nr_of_runs)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING race_id
    """, (data['raceinfo']['federation'], data['raceinfo']['sector'], data['raceinfo']['discipline'], data['raceinfo']['codex'], data['raceinfo']['racedate'], data['raceinfo']['nr_of_runs']))
    race_id = cursor.fetchone()[0]

    # Insert runs
    for run in data['runs']:
        cursor.execute("""
            INSERT INTO runs (race_id, run_nr, homologation, start_time, start_height, finish_height, vertical_height, gates, turning_gates)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING run_id
        """, (race_id, run['run_nr'], run['homologation'], run['starttime'], run['start_height'], run['finish_height'], run['vertical_height'], run['gates'], run['turning_gates']))
        run_id = cursor.fetchone()[0]

    # Insert start classes
    for sc in data['startclasses']:
        cursor.execute("""
            INSERT INTO start_classes (race_id, startclass_nr, description, desc_short, sex, year_from, year_to, nr_of_runs, nr_of_runs_eval, entry_fee, additional_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING start_class_id
        """, (race_id, sc['startclass_nr'], sc['description'], sc['desc_short'], sc['sex'], sc['year_from'], sc['year_to'], sc['nr_of_runs'], sc['nr_of_runs_eval'], sc['entry_fee'], sc['additional_fee']))
        start_class_id = cursor.fetchone()[0]

    # Insert athletes and race results (loop through starters)
    for athlete in data['starters']:
        cursor.execute("""
            INSERT INTO athletes (federation_code, firstname, surname, sex, birth_year, birth_month, birth_day, club_code, clubname)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (federation_code) DO NOTHING
            RETURNING athlete_id
        """, (athlete['federation_code'], athlete['firstname'], athlete['surname'], athlete['sex'], athlete['birth_year'], athlete['birth_month'], athlete['birth_day'], athlete['club_code'], athlete['clubname']))
        athlete_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO race_results (race_id, run_id, start_class_id, athlete_id, bib, rank, time_min, time_sec, time_thous, status_run, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (race_id, run_id, start_class_id, athlete_id, athlete['bib'], athlete['rank'], athlete['time_min'], athlete['time_sec'], athlete['time_thous'], athlete['status_run'], athlete['status']))

    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success"})





# if __name__ == '__main__':
#     app.run(debug=True)
