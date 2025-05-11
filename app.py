from flask import Flask, render_template, request, session, jsonify
import os, openai, time

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

FREE_LIMIT_VISITOR = 3
FREE_LIMIT_USER = 3
PAID_LIMIT = 90

def todays_counter():
    day = time.strftime('%Y-%m-%d')
    counter = session.get(day, 0) + 1
    session[day] = counter
    session.modified = True
    return counter

def ask_doctor_virtual(msg):
    response = openai.ChatCompletion.create(
        assistant_id=ASSISTANT_ID,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": msg}]
    )
    return response.choices[0].message["content"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user = session.get("user")
    count = todays_counter()

    if user is None and count > FREE_LIMIT_VISITOR:
        return jsonify({"need_login": True})

    if user and not user.get("subscriber") and count > FREE_LIMIT_USER:
        return jsonify({"limit_reached": True})

    if user and user.get("subscriber") and count > PAID_LIMIT:
        return jsonify({"limit_reached": True})

    reply = ask_doctor_virtual(data["message"])
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
