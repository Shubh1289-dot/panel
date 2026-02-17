from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

ADMIN_USERNAME = "FR"
ADMIN_PASSWORD = "SHUBH"

JSONBIN_API_KEY = "$2a$10$R74G8pPzaRy0kLrcmfIYO.jvMl0T8JA3XQVaRHQNqYWsyO8ltxLr."
BIN_ID = "68fef44843b1c97be983b559"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# ✅ TIMEZONE (India)
IST = ZoneInfo("Asia/Kolkata")

# ✅ EXPIRY CHECK (supports datetime)
def is_expired(expiry_str):
    try:
        expiry = datetime.fromisoformat(expiry_str)
        now = datetime.now(IST)
        return now > expiry
    except:
        return False

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
            return res.json().get("record", {})
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

# ✅ CLEANUP EXPIRED USERS (REAL FIX)
def cleanup_expired_users(data, category):
    if category in data:
        before = len(data[category])
        data[category] = [u for u in data[category] if not is_expired(u["Expiry"])]
        if len(data[category]) != before:
            save_data(data)

# ---------------------------- User Management ----------------------------

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()

    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]  # datetime-local आता है

    if category not in data:
        data[category] = []

    cleanup_expired_users(data, category)

    if any(u["Username"] == username for u in data[category]):
        return jsonify({"status": "error", "message": "Username already exists"})

    now = datetime.now(IST)

    data[category].append({
        "Username": username,
        "Password": password,
        "HWID": None,
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": now.strftime("%Y-%m-%d %H:%M")
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

    cleanup_expired_users(data, category)

    for user in data[category]:
        if user["Username"] == username and user["Password"] == password:

            if is_expired(user["Expiry"]):
                data[category] = [u for u in data[category] if u["Username"] != username]
                save_data(data)
                return jsonify({"status": "error", "message": "Account expired"})

            if user["Status"] != "Active":
                return jsonify({"status": "error", "message": "Account paused"})

            if user["HWID"] in [None, ""]:
                user["HWID"] = client_hwid
                save_data(data)
                return jsonify({"status": "success", "message": "HWID bound. Login success"})

            if user["HWID"] != client_hwid:
                return jsonify({"status": "error", "message": "HWID mismatch. Access denied"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid username or password"})

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = load_data()

    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    cleanup_expired_users(data, category)

    before = len(data[category])
    data[category] = [u for u in data[category] if u["Username"] != username]

    if len(data[category]) == before:
        return jsonify({"status": "error", "message": "User not found"})

    if save_data(data):
        return jsonify({"status": "success", "message": "User deleted"})
    return jsonify({"status": "error", "message": "Failed to update data"})

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form["category"]

    cleanup_expired_users(data, category)

    return jsonify(data.get(category, []))

# ---------------------------- Run ----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
