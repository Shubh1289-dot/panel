from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ✅ FORCE INDIA TIMEZONE
IST = pytz.timezone("Asia/Kolkata")

# Admin credentials
ADMIN_USERNAME = "FR"
ADMIN_PASSWORD = "SHUBH"

# JSONBin Config
JSONBIN_API_KEY = "$2a$10$R74G8pPzaRy0kLrcmfIYO.jvMl0T8JA3XQVaRHQNqYWsyO8ltxLr."
BIN_ID = "68fef44843b1c97be983b559"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# ✅ EXPIRY CHECK (DATE + TIME SUPPORT)
def is_expired(expiry_str):
    try:
        expiry_str = expiry_str.strip()

        if "T" in expiry_str:
            expiry_time = datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M")
        else:
            expiry_time = datetime.strptime(expiry_str, "%Y-%m-%d")

        return datetime.now(IST) >= expiry_time

    except Exception as e:
        print("EXPIRY ERROR:", expiry_str, e)
        return False


def clean_expired_users(data):
    changed = False

    for category in list(data.keys()):
        original_len = len(data[category])

        data[category] = [
            user for user in data[category]
            if not is_expired(user.get("Expiry", ""))
        ]

        if len(data[category]) != original_len:
            changed = True

    if changed:
        print("Expired users removed")
        save_data(data)

    return data

# ---------------------------- Auth Routes ----------------------------

@app.route("/")
def home():
    if session.get("logged_in"):
        return render_template("index.html")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

# ---------------------------- JSONBin Logic ----------------------------

def load_data():
    try:
        res = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)

        if res.status_code == 200:
            data = res.json().get("record", {})
            return clean_expired_users(data)   # ✅ AUTO CLEAN

        return {}

    except Exception as e:
        print("Load Error:", e)
        return {}

def save_data(data):
    try:
        res = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data)
        return res.status_code == 200

    except Exception as e:
        print("Save Error:", e)
        return False

# ---------------------------- User Management ----------------------------

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()

    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]

    if category not in data:
        data[category] = []

    if any(u["Username"] == username for u in data[category]):
        return jsonify({"status": "error", "message": "Username already exists"})

    data[category].append({
        "Username": username,
        "Password": password,
        "HWID": None,
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": datetime.now(IST).strftime("%Y-%m-%d %H:%M")  # ✅ FIXED
    })

    if save_data(data):
        return jsonify({"status": "success", "message": "User added successfully"})

    return jsonify({"status": "error", "message": "Failed to add user"})


@app.route("/client_login", methods=["POST"])
def client_login():
    data = load_data()

    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    client_hwid = request.form["hwid"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for user in data[category]:
        if user["Username"] == username and user["Password"] == password:

            if is_expired(user.get("Expiry", "")):
                data[category] = [u for u in data[category] if u["Username"] != username]
                save_data(data)
                return jsonify({"status": "error", "message": "Account expired"})

            if user["Status"] != "Active":
                return jsonify({"status": "error", "message": "Account paused"})

            if user["HWID"] in [None, ""]:
                user["HWID"] = client_hwid

                if save_data(data):
                    return jsonify({"status": "success", "message": "HWID bound. Login success"})

                return jsonify({"status": "error", "message": "Failed to bind HWID"})

            if user["HWID"] != client_hwid:
                return jsonify({"status": "error", "message": "HWID mismatch. Access denied"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid username or password"})


@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form["category"]
    return jsonify(data.get(category, []))

# ---------------------------- Run ----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
