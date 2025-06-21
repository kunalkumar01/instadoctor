from flask import Flask, render_template, request, session, jsonify
from openai import OpenAI
import os, time

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

FREE_LIMIT_VISITOR = 3

def todays_counter():
    day = time.strftime('%Y-%m-%d')
    counter = session.get(day, 0) + 1
    session[day] = counter
    session.modified = True
    return counter

def ask_doctor_virtual(msg):
    print(f"🟡 Sending to GPT: {msg}")
    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=msg
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        while True:
            status = client.beta.threads.runs.retrieve(
                run_id=run.id,
                thread_id=thread.id
            )
            if status.status == "completed":
                break
            if status.status in ["failed", "cancelled", "expired", "requires_action"]:
                raise RuntimeError(f"Run {status.status}")
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value
        print("✅ GPT Reply:", reply)
        return reply

    except Exception as e:
        print("❌ GPT ERROR:", str(e))
        return f"⚠️ Error talking to Doctor Virtual: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return render_template("chat.html")

    data = request.get_json()
    count = todays_counter()

    if count > FREE_LIMIT_VISITOR:
        return jsonify({"need_login": True})

    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "❗️Please enter a message."})

    reply = ask_doctor_virtual(user_msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    print("🚀 Starting Flask on port 8080")
    app.run(host="0.0.0.0", port=8080)
