from flask import Flask, render_template, request, session, jsonify
import os, openai, time

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "test"

FREE_LIMIT_VISITOR = 3

def todays_counter():
    day = time.strftime('%Y-%m-%d')
    counter = session.get(day, 0) + 1
    session[day] = counter
    session.modified = True
    return counter

def ask_doctor_virtual(msg):
    print(f"Sending to GPT: {msg}")
    try:
        response = openai.ChatCompletion.create(
            assistant_id=ASSISTANT_ID,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": msg}]
        )
        reply = response.choices[0].message["content"]
        print("✅ GPT Reply:", reply)
        return reply
    except Exception as e:
        print("❌ GPT ERROR:", str(e))
        return f"⚠️ Error talking to Doctor Virtual: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    count = todays_counter()

    if count > FREE_LIMIT_VISITOR:
        return jsonify({"need_login": True})

    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "❗️Please enter a message."})

    reply = ask_doctor_virtual(user_msg)
    return jsonify({"reply": reply})

