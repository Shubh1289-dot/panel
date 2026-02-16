from flask import Flask, request, jsonify, render_template
import requests
from datetime import datetime
import os

app = Flask(__name__)

JSONBIN_API_KEY = "$2a$10$R74G8pPzaRy0kLrcmfIYO.jvMl0T8JA3XQVaRHQNqYWsyO8ltxLr."
BIN_ID = "68fef44843b1c97be983b559"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# ✅ CORRECT EXPIRY LOGIC
def is_expired(expiry_str):
    try:
        if not expiry_str:
            return False

        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()

        # ✅ TODAY VALID / ONLY PAST EXPIRED
        return datetime.today().date() > expiry_date

    except Exception as e:
        print("Expiry Error:", expiry_str, e)
        return False

# ---------------- JSONBIN ----------------

def load_data():
    try:
        res = requests.get(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest",
            headers=HEADERS,
            timeout=5
        )

        if res.status_code == 200:
            return res.json().get("record", {})

        print("LOAD FAILED:", res.status_code, res.text)
        return {}

    except Exception as e:
        print("Load Error:", e)
        return {}

def save_data(data):
    try:
        res = requests.put(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}",
            headers=HEADERS,
            json=data,
            timeout=5
        )

        print("SAVE STATUS:", res.status_code)

        if res.status_code != 200:
            print("SAVE FAILED:", res.text)

        return res.status_code == 200

    except Exception as e:
        print("Save Error:", e)
        return False

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()

    category = request.form.get("category", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    expiry = request.form.get("expiry", "").strip()

    if not category or not username or not password or not expiry:
        return jsonify({"status": "error", "message": "Fill all fields"})

    if category not in data:
        data[category] = []

    if any(u["Username"] == username for u in data[category]):
        return jsonify({"status": "error", "message": "Username exists"})

    data[category].append({
        "Username": username,
        "Password": password,
        "Expiry": expiry,
        "Status": "Active",
        "HWID": None,
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })

    if save_data(data):
        return jsonify({"status": "success", "message": "User added"})

    return jsonify({"status": "error", "message": "Save failed"})

@app.route("/client_login", methods=["POST"])
def client_login():
    data = load_data()

    category = request.form.get("category", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid app"})

    for user in data[category]:

        if user["Username"] == username and user["Password"] == password:

            if is_expired(user.get("Expiry")):
                return jsonify({"status": "error", "message": "Account expired"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid credentials"})

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form.get("category", "").strip()

    valid_users = []

    for user in data.get(category, []):
        if not is_expired(user.get("Expiry")):
            valid_users.append(user)

    return jsonify(valid_users)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
