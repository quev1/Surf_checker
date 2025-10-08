# main.py
import json
from utils.api_client import get_forecast
from rich.console import Console

console = Console()

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def analyze_conditions(data, ideal):
    """Analyse les conditions journalières selon les critères idéaux."""
    results = []
    # On suppose que data est un DataFrame Pandas
    for i, row in data.iterrows():
        wave_height = row["wave_height_max"]
        wave_period = row["wave_period_max"]
        wind_dir = row.get("wave_direction_dominant", None)
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

        # Séparation matin/après-midi
        hour = row["date"].hour
        if 8 <= hour < 12:
            period = "matin"
        elif 12 <= hour < 20:
            period = "après-midi"
        else:
            continue  # Ignore les autres heures
        results.append((row["date"].strftime("%Y-%m-%d"), period, score))
    return results

def main():
    config = load_config()
    spot = config["spot"]
    ideal = config["ideal_conditions"]

    console.print(f"\n🌊 [bold cyan]Prévisions surf pour {spot['name']}[/bold cyan]\n")

    try:
        data = get_forecast(spot["lat"], spot["lng"], days=3)
        scores = analyze_conditions(data, ideal)

        # Séparation des scores par jour et période
        daily_period_scores = {}
        for day, period, score in scores:
            daily_period_scores.setdefault(day, {"matin": [], "après-midi": []})
            daily_period_scores[day][period].append(score)

        for day, periods in daily_period_scores.items():
            for period, vals in periods.items():
                if not vals:
                    continue
                avg = sum(vals) / len(vals)
                if avg > 6:
                    mood = "🌞 Excellent"
                elif avg > 4:
                    mood = "🌤️ Bon"
                else:
                    mood = "💨 Mauvais"
                console.print(f"{day} [{period}] : {mood} (score moyen {avg:.1f}/6)")
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la récupération des prévisions : {e}[/bold red]")

if __name__ == "__main__":
    main()
