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

# ---------------------------- EXPIRY LOGIC ----------------------------

def parse_expiry(expiry_str):
    try:
        return datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M")
    except:
        try:
            return datetime.strptime(expiry_str, "%Y-%m-%d")
        except:
            return None


def is_expired(expiry_str):
    expiry = parse_expiry(expiry_str)
    if not expiry:
        return False
    return datetime.now() > expiry


# ---------------------------- JSONBIN ----------------------------

def load_data_raw():
    try:
        res = requests.get(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}",
            headers=HEADERS
        )

        if res.status_code == 200:
            return res.json().get("record", {})

        print("Load Failed:", res.status_code, res.text)
        return {}

    except Exception as e:
        print("Load Error:", e)
        return {}


def save_data(data):
    try:
        res = requests.put(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}?meta=false",
            headers=HEADERS,
            json=data
        )

        print("Save Status:", res.status_code)
        return res.status_code == 200

    except Exception as e:
        print("Save Error:", e)
        return False


def clean_expired_users(data):
    changed = False
    now = datetime.now()

    for category in list(data.keys()):
        users = data.get(category, [])
        valid_users = []

        for user in users:
            expiry = parse_expiry(user.get("Expiry", ""))
            if expiry and now > expiry:
                print("AUTO DELETE:", user.get("Username"))
                changed = True
                continue

            valid_users.append(user)

        data[category] = valid_users

    if changed:
        save_data(data)

    return data


def load_data():
    data = load_data_raw()
    return clean_expired_users(data)


# ---------------------------- AUTH ----------------------------

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


# ---------------------------- USER MANAGEMENT ----------------------------

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
        "HWID": "",
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    if save_data(data):
        return jsonify({"status": "success", "message": "User added successfully"})

    return jsonify({"status": "error", "message": "Failed to add user"})


@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = load_data()

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

    return jsonify({"status": "error", "message": "Delete failed"})


@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    return jsonify(data.get(request.form["category"], []))


@app.route("/client_login", methods=["POST"])
def client_login():
    data = load_data()

    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    hwid = request.form["hwid"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for user in data[category]:

        if user["Username"] == username and user["Password"] == password:

            if is_expired(user["Expiry"]):
                data[category] = [u for u in data[category] if u["Username"] != username]
                save_data(data)
                return jsonify({"status": "error", "message": "Expired"})

            if user["Status"] != "Active":
                return jsonify({"status": "error", "message": "Paused"})

            if not user["HWID"]:
                user["HWID"] = hwid
                save_data(data)
                return jsonify({"status": "success", "message": "HWID bound"})

            if user["HWID"] != hwid:
                return jsonify({"status": "error", "message": "HWID mismatch"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid credentials"})


# ---------------------------- RUN ----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
