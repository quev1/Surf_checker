from flask import Flask, render_template
import json
from utils.api_client import get_forecast

app = Flask(__name__)

# Analyse adaptée pour tableau

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def analyze_conditions(data, ideal):
    results = []
    for i, row in data.iterrows():
        wave_height = row["wave_height"]
        wave_period = row["wave_period"]
        wind_dir = row.get("wave_direction", None)
        wind_dir_str = None
        if wind_dir is not None:
            dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            wind_dir_str = dirs[int((wind_dir + 22.5) % 360 / 45)]
        score = 0
        if ideal["swell_height_min"] <= wave_height <= ideal["swell_height_max"]:
            score += 2
        if wave_period >= ideal["swell_period_min"]:
            score += 2
        if wind_dir_str and wind_dir_str in ideal["wind_direction_good"]:
            score += 2
        hour = row["date"].hour
        if 8 <= hour < 12:
            period = "Matin"
        elif 12 <= hour < 20:
            period = "Après-midi"
        else:
            continue
        results.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "period": period,
            "wave_height": wave_height,
            "wave_period": wave_period,
            "wave_dir": wind_dir_str,
            "score": score
        })
    return results

@app.route("/")
def index():
    config = load_config()
    spot = config["spot"]
    ideal = config["ideal_conditions"]
    try:
        data = get_forecast(spot["lat"], spot["lng"], days=3)
        results = analyze_conditions(data, ideal)
        # Regroupement par jour et période
        table = {}
        for r in results:
            day = r["date"]
            period = r["period"]
            table.setdefault(day, {})[period] = r
        return render_template("surf_table.html", spot=spot, table=table)
    except Exception as e:
        return f"Erreur : {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
