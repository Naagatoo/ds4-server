from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import string

app = Flask(__name__)

DB_NAME = "licenses.db"
ADMIN_SECRET = "DS4_ADMIN_2026_ULTRA_SECRET"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT UNIQUE,
        username TEXT,
        subscription TEXT,
        created_at TEXT,
        expires_at TEXT,
        last_login TEXT,
        hwid TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()


def generate_key():
    return "-".join(
        "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        for _ in range(4)
    )


def format_remaining_time(expires_at_str):
    if not expires_at_str:
        return "Lifetime"

    expires_at = datetime.fromisoformat(expires_at_str)
    now = datetime.now()

    if now >= expires_at:
        return "Expirée"

    delta = expires_at - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    return f"{days}j {hours}h {minutes}min"


@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM licenses WHERE license_key=?", (key,))
    row = cur.fetchone()

    if not row:
        return jsonify({"valid": False})

    if row["expires_at"]:
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.now() >= expires:
            return jsonify({"valid": False, "reason": "expired"})

    if row["hwid"]:
        if row["hwid"] != hwid:
            return jsonify({"valid": False, "reason": "already_used_on_other_pc"})
    else:
        cur.execute("UPDATE licenses SET hwid=? WHERE license_key=?", (hwid, key))
        conn.commit()

    now = datetime.now().isoformat()
    cur.execute("UPDATE licenses SET last_login=? WHERE license_key=?", (now, key))
    conn.commit()

    return jsonify({
        "valid": True,
        "username": row["username"],
        "subscription": row["subscription"],
        "expires_at": row["expires_at"],
        "time_left": format_remaining_time(row["expires_at"]),
        "last_login": now
    })


@app.route("/create-license", methods=["POST"])
def create_license():
    data = request.json

    if data.get("admin_secret") != ADMIN_SECRET:
        return jsonify({"ok": False})

    username = data.get("username", "client")
    subscription = data.get("subscription", "default")
    duration = data.get("duration_days")

    created_at = datetime.now()

    if duration:
        expires_at = created_at + timedelta(days=int(duration))
        expires_str = expires_at.isoformat()
    else:
        expires_str = None

    key = generate_key()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO licenses (license_key, username, subscription, created_at, expires_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        key,
        username,
        subscription,
        created_at.isoformat(),
        expires_str
    ))

    conn.commit()

    return jsonify({"ok": True, "license_key": key})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)