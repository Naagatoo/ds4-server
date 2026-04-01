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


def format_display_date(iso_date):
    if not iso_date:
        return "Lifetime"
    dt = datetime.fromisoformat(iso_date)
    return dt.strftime("%d/%m/%Y à %H:%M")


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "ok": True,
        "message": "DS4 server online"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "status": "healthy"
    }), 200


@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "message": "Use POST with key and hwid"
        }), 200

    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    hwid = (data.get("hwid") or "").strip()

    if not key or not hwid:
        return jsonify({"valid": False, "reason": "missing_data"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM licenses WHERE license_key = ?", (key,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"valid": False, "reason": "invalid_key"}), 200

    if row["active"] != 1:
        conn.close()
        return jsonify({"valid": False, "reason": "disabled"}), 200

    if row["expires_at"]:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now() >= expires_at:
            conn.close()
            return jsonify({"valid": False, "reason": "expired"}), 200

    if row["hwid"]:
        if row["hwid"] != hwid:
            conn.close()
            return jsonify({"valid": False, "reason": "already_used_on_other_pc"}), 200
    else:
        cur.execute("UPDATE licenses SET hwid = ? WHERE license_key = ?", (hwid, key))
        conn.commit()

    now_str = datetime.now().isoformat(timespec="seconds")
    cur.execute("UPDATE licenses SET last_login = ? WHERE license_key = ?", (now_str, key))
    conn.commit()

    response = {
        "valid": True,
        "username": row["username"],
        "subscription": row["subscription"],
        "expires_at": format_display_date(row["expires_at"]),
        "time_left": format_remaining_time(row["expires_at"]),
        "last_login": format_display_date(now_str)
    }

    conn.close()
    return jsonify(response), 200


@app.route("/create-license", methods=["POST"])
def create_license():
    data = request.get_json(silent=True) or {}

    admin_secret = (data.get("admin_secret") or "").strip()
    username = (data.get("username") or "client").strip()
    subscription = (data.get("subscription") or "default").strip()
    duration_days = data.get("duration_days")

    if admin_secret != ADMIN_SECRET:
        return jsonify({"ok": False, "reason": "unauthorized"}), 403

    created_at = datetime.now().isoformat(timespec="seconds")

    if duration_days is None:
        expires_at = None
    else:
        try:
            duration_days = int(duration_days)
            expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat(timespec="seconds")
        except Exception:
            return jsonify({"ok": False, "reason": "invalid_duration"}), 400

    license_key = generate_key()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO licenses (license_key, username, subscription, created_at, expires_at, last_login, hwid, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        license_key,
        username,
        subscription,
        created_at,
        expires_at,
        None,
        None
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "license_key": license_key,
        "username": username,
        "subscription": subscription,
        "expires_at": format_display_date(expires_at) if expires_at else "Lifetime"
    }), 200


@app.route("/reset-hwid", methods=["POST"])
def reset_hwid():
    data = request.get_json(silent=True) or {}
    admin_secret = (data.get("admin_secret") or "").strip()
    key = (data.get("key") or "").strip()

    if admin_secret != ADMIN_SECRET:
        return jsonify({"ok": False, "reason": "unauthorized"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE licenses SET hwid = NULL WHERE license_key = ?", (key,))
    conn.commit()
    updated = cur.rowcount
    conn.close()

    return jsonify({"ok": updated > 0}), 200


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)