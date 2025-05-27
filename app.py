from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import pooling, Error
import requests

app = Flask(__name__)

# Config DB
dbconfig = {
    "host": "sql.freedb.tech",
    "user": "freedb_Paulap",
    "password": "j&7dsA5XZ95DQdg",
    "database": "freedb_Weather"
}

connection_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)

def get_connection():
    return connection_pool.get_connection()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/harta')
def harta():
    return render_template('map.html')

# API: CRUD

@app.route('/api/weather', methods=['GET'])
def get_all():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, oras FROM weather")
        data = cursor.fetchall()
        return jsonify(data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/weather/<int:item_id>', methods=['GET'])
def get_one(item_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, oras FROM weather WHERE id = %s", (item_id,))
        row = cursor.fetchone()
        if row:
            return jsonify(row), 200
        return jsonify({"error": "Datele nu au fost găsite"}), 404
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/weather', methods=['POST'])
def create_weather():
    data = request.get_json()
    if not data or not {"id", "oras"}.issubset(data):
        return jsonify({"error": "Date lipsă sau incorecte"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO weather (id, oras) VALUES (%s, %s)", (data["id"], data["oras"]))
        conn.commit()
        return jsonify({"message": "Înregistrare adăugată"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/weather/<int:item_id>', methods=['PUT'])
def update_weather(item_id):
    data = request.get_json()
    if not data or "oras" not in data:
        return jsonify({"error": "Nicio informație de actualizat"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE weather SET oras=%s WHERE id=%s", (data["oras"], item_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "ID inexistent"}), 404
        return jsonify({"message": "Înregistrare actualizată"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/weather/<int:item_id>', methods=['DELETE'])
def delete_weather(item_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM weather WHERE id = %s", (item_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "ID inexistent"}), 404
        return jsonify({"message": "Șters cu succes"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/weather', methods=['DELETE'])
def delete_all():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM weather")
        conn.commit()
        return jsonify({"message": "Toate datele au fost șterse"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/weather', methods=['PUT'])
def replace_all():
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Datele trebuie să fie o listă"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM weather")
        for entry in data:
            if {"id", "oras"} <= entry.keys():
                cursor.execute("INSERT INTO weather (id, oras) VALUES (%s, %s)", (entry["id"], entry["oras"]))
        conn.commit()
        return jsonify({"message": "Colecție înlocuită"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Weather API
WEATHER_API_KEY = "f2f87e92b030dc13fc82e5353085fb6a"

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    city = request.args.get('city')

    if not city:
        return jsonify({"error": "Orașul nu a fost specificat."}), 400

    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ro"
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Nu s-a putut obține prognoza pentru {city}."}), 400

        data = response.json()
        daily_forecast = {}

        for entry in data["list"]:
            date = entry["dt_txt"].split(" ")[0]
            if date not in daily_forecast:
                daily_forecast[date] = {
                    "data": date,
                    "temperatura": entry["main"]["temp"],
                    "umiditate": entry["main"]["humidity"],
                    "descriere": entry["weather"][0]["description"]
                }
            if len(daily_forecast) == 5:
                break

        return jsonify({
            "oras": city,
            "prognoza": list(daily_forecast.values())
        }), 200

    except Exception as e:
        return jsonify({"error": f"Eroare: {str(e)}"}), 500

# Atracții turistice + hartă meteo

TOURISM_API_KEY = "5ae2e3f221c38a28845f05b641fe720a2536b1e0c8fba28d8b449068"

def get_tourist_attractions(lat, lon, radius=10000, limit=10):
    try:
        url = f"https://api.opentripmap.com/0.1/en/places/radius?radius={radius}&lon={lon}&lat={lat}&limit={limit}&apikey={TOURISM_API_KEY}&format=json"
        response = requests.get(url)
        if response.status_code != 200:
            return []

        data = response.json()
        attractions = []
        for item in data:
            if item.get("name") and item.get("point"):
                attractions.append({
                    "nume": item.get("name"),
                    "tip": item.get("kinds"),
                    "lat": item.get("point", {}).get("lat"),
                    "lon": item.get("point", {}).get("lon")
                })
        return attractions
    except Exception:
        return []

@app.route('/api/mapdata', methods=['GET'])
def get_map_data():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT oras FROM weather")
        cities = [row["oras"] for row in cursor.fetchall()]
    except Error as e:
        return jsonify({"error": "Eroare DB: " + str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    result = []

    for city in cities:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url)
            if response.status_code != 200:
                continue
            data = response.json()
            lat = data["coord"]["lat"]
            lon = data["coord"]["lon"]

            attractions = get_tourist_attractions(lat, lon)

            result.append({
                "oras": city,
                "lat": lat,
                "lon": lon,
                "temp": data["main"]["temp"],
                "descriere": data["weather"][0]["description"],
                "icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
                "atractii": attractions
            })
        except Exception:
            continue

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)
