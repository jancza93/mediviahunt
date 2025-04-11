from flask import Flask, request, jsonify, render_template, redirect, url_for
import json, os, string, random
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "sessions.json"

DEFAULT_PRICES = {
    "uh": 145,
    "sd": 330,
    "ice": 125,
    "hmm": 85,
    "explo": 260,
    "pot": 850,
    "gfb": 190,
    "heavy ammo": 55,
    "piercing arrows": 12,
    "hunting arrows": 4,
    "piercing bolts": 15,
    "hunting bolts": 5,
    "purity ring [min]": 234,
    "ring": 234, # Dodaj alias dla "purity ring [min]" jeśli użytkownik wpisze krócej
    "gold": 1 # Przyjmujemy, że "gold" ma wartość 1
}

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

def parse_supplies(s: str):
    result = {}
    for part in s.split(','):
        try:
            num, name = part.strip().split(' ', 1)
            result[name.lower()] = int(num)
        except ValueError:
            continue
        except IndexError:
            continue
    return result

def parse_loot(s: str):
    loot = {}
    for item in s.split(','):
        try:
            parts = item.strip().split(' ')
            if len(parts) >= 3:
                amount = int(parts[0])
                name = " ".join(parts[1:-1]).lower() # Obsługa nazw wieloczłonowych
                value = int(parts[-1])
                loot[name] = {"amount": amount, "value": value}
            elif len(parts) == 2:
                amount = int(parts[0])
                name = parts[1].lower()
                # Jeśli nie podano wartości, możemy spróbować użyć domyślnej ceny
                if name in DEFAULT_PRICES:
                    loot[name] = {"amount": amount, "value": DEFAULT_PRICES.get(name, 0)}
                else:
                    print(f"Uwaga: Nieznany przedmiot '{name}' bez podanej wartości.")
            elif len(parts) == 3: # ilość nazwa wartość
                amount = int(parts[0])
                name = parts[1].lower()
                value = int(parts[2])
                loot[name] = {"amount": amount, "value": value}
        except ValueError:
            continue
    return loot

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
    loot_str = request.form.get('loot', '') # Pobierz dane o łupie

    data = load_data()
    if session_id in data:
        data[session_id]['players'][name] = {"start": start, "end": end, "loot": parse_loot(loot_str)}
        save_data(data)
    return redirect(url_for('summary', session_id=session_id))

@app.route('/summary/<session_id>')
def summary(session_id):
    data = load_data()
    session = data.get(session_id, {})
    used_run_data = {}
    player_costs = {}
    player_profit = {}
    total_session_cost = 0
    total_session_profit = 0

    for name, pdata in session.get("players", {}).items():
        start_supplies = parse_supplies(pdata.get("start", ""))
        end_supplies = parse_supplies(pdata.get("end", ""))
        player_loot = pdata.get("loot", {})
        used_run = {}
        player_cost = 0
        player_earned = 0

        # Oblicz zużycie i koszt
        all_keys = set(start_supplies.keys()) | set(end_supplies.keys())
        for item_name in all_keys:
            start_count = start_supplies.get(item_name, 0)
            end_count = end_supplies.get(item_name, 0)
            used_count = start_count - end_count
            if used_count > 0 and item_name in DEFAULT_PRICES:
                used_run[item_name] = used_count
                player_cost += used_count * DEFAULT_PRICES[item_name]

        used_run_data[name] = used_run
        player_costs[name] = player_cost
        total_session_cost += player_cost

        # Oblicz zysk
        for item_name, loot_data in player_loot.items():
            player_earned += loot_data.get("amount", 0) * loot_data.get("value", 0)

        player_profit[name] = player_earned
        total_session_profit += player_earned

    net_session_profit = total_session_profit - total_session_cost

    return render_template(
        "summary.html",
        session=session,
        session_id=session_id,
        used_run_data=used_run_data,
        player_costs=player_costs,
        player_profit=player_profit,
        total_session_cost=total_session_cost,
        total_session_profit=total_session_profit,
        net_session_profit=net_session_profit,
        default_prices=DEFAULT_PRICES
    )

@app.route('/data/<session_id>')
def data_json(session_id):
    data = load_data()
    return jsonify(data.get(session_id, {}))

if __name__ == '__main__':
    app.run(debug=True)
