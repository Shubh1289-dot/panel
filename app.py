from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import threading
import time
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

IST = ZoneInfo("Asia/Kolkata")

ADMIN_USERNAME = "FR"
ADMIN_PASSWORD = "SHUBH"

JSONBIN_API_KEY = "$2a$10$R74G8pPzaRy0kLrcmfIYO.jvMl0T8JA3XQVaRHQNqYWsyO8ltxLr."
BIN_ID = "68fef44843b1c97be983b559"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# ✅ EXPIRY CHECK (MINUTE ACCURATE)
def is_expired(expiry_str):
    try:
        expiry_str = expiry_str.replace("T", " ")
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M")
        now = datetime.now(IST)
        return now >= expiry
    except Exception as e:
        print("Expiry Parse Error:", expiry_str, e)
        return False

# ---------------- JSONBIN ----------------

def load_data_raw():
    try:
        res = requests.get(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest",
            headers=HEADERS
        )
        if res.status_code == 200:
            return res.json().get("record", {})
        return {}
    except Exception as e:
        print("Load Error:", e)
        return {}

def save_data(data):
    try:
        res = requests.put(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}",
            headers=HEADERS,
            json=data
        )
        return res.status_code == 200
    except Exception as e:
        print("Save Error:", e)
        return False

# ---------------- CLEANUP ----------------

def cleanup_all(data):
    changed = False
    for category in data:
        before = len(data[category])
        data[category] = [u for u in data[category] if not is_expired(u["Expiry"])]
        if len(data[category]) != before:
            changed = True
    if changed:
        save_data(data)
        print("Expired users cleaned")

def background_cleaner():
    while True:
        try:
            data = load_data_raw()
            cleanup_all(data)
        except Exception as e:
            print("Cleaner Error:", e)

        time.sleep(60)  # हर 60 sec

# ---------------- AUTH ----------------

@app.route("/")
def home():
    if session.get("logged_in"):
        return render_template("index.html")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

# ---------------- USERS ----------------

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data_raw()
    cleanup_all(data)

    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]

    if category not in data:
        data[category] = []

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

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = load_data_raw()
    cleanup_all(data)

    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    before = len(data[category])
    data[category] = [u for u in data[category] if u["Username"] != username]

    if len(data[category]) == before:
        return jsonify({"status": "error", "message": "User not found"})

    if save_data(data):
        return jsonify({"status": "success", "message": "User deleted"})
    return jsonify({"status": "error", "message": "Failed to update data"})

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data_raw()
    cleanup_all(data)

    category = request.form["category"]
    return jsonify(data.get(category, []))

@app.route("/client_login", methods=["POST"])
def client_login():
    data = load_data_raw()
    cleanup_all(data)

    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    client_hwid = request.form["hwid"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for user in data[category]:
        if user["Username"] == username and user["Password"] == password:

            if is_expired(user["Expiry"]):
                return jsonify({"status": "error", "message": "Account expired"})

            if user["Status"] != "Active":
                return jsonify({"status": "error", "message": "Account paused"})

            if not user["HWID"]:
                user["HWID"] = client_hwid
                save_data(data)
                return jsonify({"status": "success", "message": "HWID bound. Login success"})

            if user["HWID"] != client_hwid:
                return jsonify({"status": "error", "message": "HWID mismatch"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid credentials"})

# ---------------- RUN ----------------

if __name__ == "__main__":
    threading.Thread(target=background_cleaner, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
