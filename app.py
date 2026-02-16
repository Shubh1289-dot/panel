from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests
from datetime import datetime
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

# ✅ SAFE EXPIRY CHECK (never crashes)
def is_expired(expiry_str):
    try:
        if not expiry_str:
            return False

        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        return datetime.today().date() >= expiry

    except Exception as e:
        print("Expiry Error:", expiry_str, e)
        return False

# ---------------- JSONBin ----------------

def load_data():
    try:
        res = requests.get(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest",
            headers=HEADERS
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
            json=data
        )

        print("SAVE STATUS:", res.status_code)

        if res.status_code != 200:
            print("SAVE FAILED:", res.text)

        return res.status_code == 200

    except Exception as e:
        print("Save Error:", e)
        return False

# ---------------- Auth ----------------

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

# ---------------- Users ----------------

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()

    category = request.form.get("category", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    expiry = request.form.get("expiry", "").strip()

    if not category or not username or not password:
        return jsonify({"status": "error", "message": "Missing fields"})

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
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })

    if save_data(data):
        return jsonify({"status": "success", "message": "User added successfully"})

    return jsonify({"status": "error", "message": "JSONBin save failed"})

@app.route("/client_login", methods=["POST"])
def client_login():
    data = load_data()

    category = request.form.get("category", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    client_hwid = request.form.get("hwid", "").strip()

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for user in data[category]:

        if user["Username"] == username and user["Password"] == password:

            # ✅ AUTO DELETE IF EXPIRED
            if is_expired(user.get("Expiry")):
                data[category] = [u for u in data[category] if u["Username"] != username]
                save_data(data)

                return jsonify({"status": "error", "message": "Account expired"})

            if user.get("Status") != "Active":
                return jsonify({"status": "error", "message": "Account paused"})

            if user.get("HWID") in [None, ""]:
                user["HWID"] = client_hwid

                if save_data(data):
                    return jsonify({"status": "success", "message": "HWID bound. Login success"})

                return jsonify({"status": "error", "message": "Failed to bind HWID"})

            if user.get("HWID") != client_hwid:
                return jsonify({"status": "error", "message": "HWID mismatch"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid username or password"})

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form.get("category", "").strip()

    valid_users = []

    for u in data.get(category, []):
        if not is_expired(u.get("Expiry")):
            valid_users.append(u)

    return jsonify(valid_users)

# ---------------- Run ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
