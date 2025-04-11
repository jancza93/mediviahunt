from flask import Flask, request, jsonify, render_template, redirect, url_for
import json, os, string, random
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "sessions.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_session_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/create', methods=['POST'])
def create():
    data = load_data()
    session_id = generate_session_id()
    data[session_id] = {
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "players": {}
    }
    save_data(data)
    return redirect(url_for('join', session_id=session_id))

@app.route('/join/<session_id>')
def join(session_id):
    return render_template("join.html", session_id=session_id)

@app.route('/submit', methods=['POST'])
def submit():
    session_id = request.form['session_id']
    name = request.form['name']
    start = request.form['start']
    end = request.form['end']

    data = load_data()
    if session_id in data:
        data[session_id]['players'][name] = {"start": start, "end": end}
        save_data(data)
    return redirect(url_for('summary', session_id=session_id))

def parse_supplies(s: str):
    result = {}
    for part in s.split(','):
        try:
            num, name = part.strip().split(' ', 1)
            result[name.lower()] = int(num)
        except:
            continue
    return result

@app.route('/summary/<session_id>')
def summary(session_id):
    data = load_data()
    session = data.get(session_id, {})
    used = {}

    for name, pdata in session.get("players", {}).items():
        start = parse_supplies(pdata.get("start", ""))
        end = parse_supplies(pdata.get("end", ""))
        used_run = {}

        all_keys = set(start.keys()) | set(end.keys())
        for k in all_keys:
            used_run[k] = start.get(k, 0) - end.get(k, 0)

        used[name] = used_run

    return render_template("summary.html", session=session, session_id=session_id, used_run_data=used)

@app.route('/data/<session_id>')
def data_json(session_id):
    data = load_data()
    return jsonify(data.get(session_id, {}))

if __name__ == '__main__':
    app.run(debug=True)
