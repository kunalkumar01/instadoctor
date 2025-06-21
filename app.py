from flask import Flask, render_template, request, session, jsonify, redirect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import os, time, sqlite3

# Validate environment configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")
if not ASSISTANT_ID:
    raise RuntimeError("ASSISTANT_ID environment variable is required")

# Initialize OpenAI client with secure API key
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "secret"

DB_PATH = os.path.join(os.path.dirname(__file__), "instadoctor.db")

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )"""
        )

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

init_db()

FREE_LIMIT_VISITOR = 3

def todays_counter():
    day = time.strftime('%Y-%m-%d')
    counter = session.get(day, 0) + 1
    session[day] = counter
    session.modified = True
    return counter

def ask_doctor_virtual(msg, thread_id, file_ids=None):
    print(f"🟡 Sending to GPT: {msg}")
    try:
        attachments = None
        if file_ids:
            attachments = [
                {"file_id": fid, "tools": [{"type": "file_search"}]}
                for fid in file_ids
            ]

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=msg,
            attachments=attachments,
        )
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        while True:
            status = client.beta.threads.runs.retrieve(
                run_id=run.id,
                thread_id=thread_id
            )
            if status.status == "completed":
                break
            if status.status in ["failed", "cancelled", "expired", "requires_action"]:
                raise RuntimeError(f"Run {status.status}")
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        reply = messages.data[0].content[0].text.value
        print("✅ GPT Reply:", reply)
        return reply

    except Exception as e:
        print("❌ GPT ERROR:", str(e))
        return f"⚠️ Error talking to Doctor Virtual: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html", logged_in=bool(session.get("user_id")))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("signup.html", error="All fields required")
        hashed = generate_password_hash(password)
        try:
            with get_db() as db:
                cur = db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed),
                )
                user_id = cur.lastrowid
            session["user_id"] = user_id
            session.modified = True
            return redirect("/chat")
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Username taken")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username=?", (username,)
            ).fetchone()
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid credentials")
        session["user_id"] = user["id"]
        session.modified = True
        return redirect("/chat")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/intake", methods=["GET", "POST"])
def intake():
    if request.method == "POST":
        session["intake"] = {
            "name": request.form.get("name", ""),
            "age": request.form.get("age", ""),
            "gender": request.form.get("gender", ""),
            "symptoms": request.form.get("symptoms", ""),
            "duration": request.form.get("duration", ""),
        }
        session["intake_submitted"] = True
        session["intake_used"] = False
        session.modified = True
        return redirect("/chat")
    return render_template("intake.html")

@app.route("/upload", methods=["POST"])
def upload():
    thread_id = session.get("thread_id")
    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
        session["thread_id"] = thread_id
        session.modified = True

    file_ids = session.get("file_ids", [])
    uploaded = request.files.getlist("file")
    new_ids = []
    for f in uploaded:
        if not f:
            continue
        filename = secure_filename(f.filename)
        openai_file = client.files.create(file=(filename, f.stream, f.mimetype), purpose="assistants")
        new_ids.append(openai_file.id)
    if new_ids:
        file_ids.extend(new_ids)
        session["file_ids"] = file_ids
        session.modified = True
    return jsonify({"uploaded": new_ids})

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        if not session.get("intake_submitted"):
            return redirect("/intake")
        return render_template("chat.html", logged_in=bool(session.get("user_id")))

    data = request.get_json()
    if not session.get("user_id"):
        count = todays_counter()
        if count > FREE_LIMIT_VISITOR:
            return jsonify({"need_login": True})

    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "❗️Please enter a message."})

    if session.get("intake_submitted") and not session.get("intake_used"):
        info = session.get("intake", {})
        prefix = (
            f"Patient Info:\n"
            f"Name: {info.get('name')}\n"
            f"Age: {info.get('age')}\n"
            f"Gender: {info.get('gender')}\n"
            f"Symptoms: {info.get('symptoms')}\n"
            f"Duration: {info.get('duration')}\n"
        )
        user_msg = prefix + "\n" + user_msg
        session["intake_used"] = True
        session.modified = True

    thread_id = session.get("thread_id")
    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
        session["thread_id"] = thread_id
        session.modified = True

    file_ids = session.get("file_ids")
    reply = ask_doctor_virtual(user_msg, thread_id, file_ids)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    print("🚀 Starting Flask on port 8080")
    app.run(host="0.0.0.0", port=8080)
