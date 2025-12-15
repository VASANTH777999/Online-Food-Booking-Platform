import json
import os
import sys
import threading
import webbrowser
import sqlite3
import hashlib
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(ROOT_DIR, "onlinefoodbookings.csv")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
DB_PATH = os.path.join(ROOT_DIR, "user_records.db")

# --- Database helpers ---
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()

def hash_password(p):
    return hashlib.sha256((p or "").encode("utf-8")).hexdigest()

def db_create_user(name, email, password):
    if not email:
        return None, "email_required"
    if not password:
        return None, "password_required"
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(name, email, password_hash, created_at) VALUES(?,?,?,?)",
            (name, email, hash_password(password), int(time.time()))
        )
        conn.commit()
        user_id = cur.lastrowid
        return user_id, None
    except sqlite3.IntegrityError:
        return None, "email_exists"
    finally:
        conn.close()

def db_verify_user(email, password):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if not row:
            return None
        user_id, pw_hash = row
        return user_id if pw_hash == hash_password(password) else None
    finally:
        conn.close()

def db_create_session(user_id):
    token = secrets.token_hex(16)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO sessions(token, user_id, created_at) VALUES(?,?,?)", (token, user_id, int(time.time())))
        conn.commit()
        return token
    finally:
        conn.close()

def db_get_user_by_token(token):
    if not token:
        return None
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT u.id, u.name, u.email FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=?", (token,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "email": row[2]}
    finally:
        conn.close()

def db_get_user_by_id(user_id):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "email": row[2]}
    finally:
        conn.close()


def read_csv_as_dicts(csv_path):
    items = []
    if not os.path.exists(csv_path):
        return items
    import csv
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize types where helpful
            if 'Cost' in row:
                try:
                    row['Cost'] = int(row['Cost'])
                except Exception:
                    pass
            if 'Rating' in row:
                try:
                    row['Rating'] = float(row['Rating'])
                except Exception:
                    pass
            items.append(row)
    return items


BOOKINGS = []
USERS = {}


class AppHandler(BaseHTTPRequestHandler):
    server_version = "ReserV9/1.0"

    def _set_headers(self, status=200, content_type="text/html"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Root redirects to signup page
        if path == "/" or path == "/index.html":
            return self._redirect_to("/signup")
        if path == "/signup":
            return self._serve_template("signup.html")
        if path == "/login":
            return self._serve_template("login.html")
        if path == "/dashboard":
            return self._serve_template("dashboard.html")
        if path == "/explore":
            return self._serve_index()
        if path in ("/favicon.svg", "/mermaidchart-logo.svg", "/logo.jpg", "/minilogo.jpg"):
            return self._serve_root_asset(path[1:])
        if path == "/logo.jpeg":
            return self._serve_root_alias("logo.jpg")
        if path == "/minilogo.jpeg":
            return self._serve_root_alias("minilogo.jpg")
        if path.startswith("/static/"):
            return self._serve_static(path)
        if path == "/api/restaurants":
            return self._api_restaurants()
        # verify-login removed per new workflow
        if path == "/api/me":
            return self._api_me(qs)
        if path == "/api/bookings":
            return self._api_bookings(qs)

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def _redirect_to(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/book":
            return self._api_book()
        if path == "/api/signup":
            return self._api_signup()
        if path == "/api/login":
            return self._api_login()
        if path == "/api/logout":
            return self._api_logout()

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def _serve_index(self):
        index_path = os.path.join(TEMPLATES_DIR, "index.html")
        if not os.path.exists(index_path):
            self._set_headers(200, "text/plain")
            self.wfile.write(b"ReserV9 server is running, but index.html was not found.")
            return
        try:
            with open(index_path, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(content)
        except Exception as e:
            self._set_headers(500, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _serve_template(self, name):
        p = os.path.join(TEMPLATES_DIR, name)
        if not os.path.exists(p):
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Template not found"}).encode("utf-8"))
            return
        try:
            with open(p, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(content)
        except Exception as e:
            self._set_headers(500, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _serve_static(self, path):
        rel = path[len("/static/"):]  # remove prefix
        fs_path = os.path.join(STATIC_DIR, rel)
        if not os.path.exists(fs_path):
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Static file not found"}).encode("utf-8"))
            return
        try:
            # Basic content type detection
            if fs_path.endswith(".js"):
                ctype = "application/javascript"
            elif fs_path.endswith(".css"):
                ctype = "text/css"
            elif fs_path.endswith(".svg"):
                ctype = "image/svg+xml"
            elif fs_path.endswith(".json"):
                ctype = "application/json"
            else:
                ctype = "application/octet-stream"
            with open(fs_path, "rb") as f:
                content = f.read()
            self._set_headers(200, ctype)
            self.wfile.write(content)
        except Exception as e:
            self._set_headers(500, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _serve_root_asset(self, filename):
        fs_path = os.path.join(ROOT_DIR, filename)
        if not os.path.exists(fs_path):
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Asset not found"}).encode("utf-8"))
            return
        try:
            with open(fs_path, "rb") as f:
                content = f.read()
            head = content[:64]
            if b"<svg" in head:
                ctype = "image/svg+xml"
            elif head.startswith(b"\xFF\xD8") or b"JFIF" in head:
                ctype = "image/jpeg"
            else:
                ctype = "application/octet-stream"
            self._set_headers(200, ctype)
            self.wfile.write(content)
        except Exception as e:
            self._set_headers(500, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _serve_root_alias(self, source_filename):
        return self._serve_root_asset(source_filename)

    def _api_restaurants(self):
        try:
            items = read_csv_as_dicts(CSV_PATH)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"data": items}).encode("utf-8"))
        except Exception as e:
            self._set_headers(500, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _api_verify_login(self, token):
        # deprecated
        self._set_headers(410, "application/json")
        self.wfile.write(json.dumps({"error": "verify-login deprecated"}).encode("utf-8"))

    def _api_me(self, qs):
        token = (qs.get("token", [""])[0] or "").strip()
        profile = db_get_user_by_token(token)
        self._set_headers(200, "application/json")
        self.wfile.write(json.dumps({"token": token or "guest", "profile": profile}).encode("utf-8"))

    def _api_book(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode('utf-8'))
            BOOKINGS.append(payload)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "booked", "data": payload}).encode("utf-8"))
        except Exception as e:
            self._set_headers(400, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _api_bookings(self, qs):
        user = (qs.get("user", [""])[0] or "").strip()
        if user:
            data = [b for b in BOOKINGS if (b.get("user") == user)]
        else:
            data = BOOKINGS
        self._set_headers(200, "application/json")
        self.wfile.write(json.dumps({"data": data}).encode("utf-8"))

    def _api_signup(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode('utf-8'))
            name = (payload.get("name") or "").strip() or "User"
            email = (payload.get("email") or "").strip()
            password = (payload.get("password") or "").strip()
            user_id, err = db_create_user(name, email, password)
            if err:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"ok": False, "error": err}).encode("utf-8"))
                return
            token = db_create_session(user_id)
            profile = {"id": user_id, "name": name, "email": email}
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True, "token": token, "profile": profile}).encode("utf-8"))
        except Exception as e:
            self._set_headers(400, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _api_login(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode('utf-8'))
            email = (payload.get("email") or "").strip()
            password = (payload.get("password") or "").strip()
            user_id = db_verify_user(email, password)
            if not user_id:
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"ok": False, "error": "invalid_credentials"}).encode("utf-8"))
                return
            token = db_create_session(user_id)
            profile = db_get_user_by_id(user_id)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True, "token": token, "profile": profile}).encode("utf-8"))
        except Exception as e:
            self._set_headers(400, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _api_logout(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode('utf-8'))
            token = (payload.get("token") or "").strip()
            if token:
                conn = get_conn()
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM sessions WHERE token=?", (token,))
                    conn.commit()
                finally:
                    conn.close()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        except Exception as e:
            self._set_headers(400, "application/json")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def run_server(port=5000):
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    legacy = os.path.join(ROOT_DIR, "Restaurant_database.csv")
    if not os.path.exists(CSV_PATH) and os.path.exists(legacy):
        try:
            with open(legacy, "rb") as src, open(CSV_PATH, "wb") as dst:
                dst.write(src.read())
        except Exception:
            pass
    init_db()
    server = HTTPServer(("127.0.0.1", port), AppHandler)
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    print(f"ReserV9 server running at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    # Allow optional custom port: python ReserV9.py 8080
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass
    run_server(port)


