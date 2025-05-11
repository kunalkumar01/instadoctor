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
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_doctor_virtual(msg):
    print(f"🟡 Sending to GPT: {msg}")
    try:
        thread = client.beta.threads.create()
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
            instructions="You are Doctor Virtual. Help the user medically."
        )
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=msg
        )

        # Poll until run is complete
        while True:
            status = client.beta.threads.runs.retrieve(run.id, thread_id=thread.id)
            if status.status == "completed":
                break
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        answer = messages.data[0].content[0].text.value
        print("✅ GPT Reply:", answer)
        return answer

    except Exception as e:
        print("❌ GPT ERROR:", str(e))
        return f"⚠️ Error talking to Doctor Virtual: {str(e)}"

        reply = response.choices[0].message["content"]
        print("✅ GPT Reply:", reply)
        return reply
    except Exception as e:
        print("❌ GPT ERROR:", str(e))
        return f"⚠️ Error talking to Doctor Virtual: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

# everything above stays the same...

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

# ✅ VERY IMPORTANT: this must be included and indented
if __name__ == "__main__":
    print("🚀 Starting Flask app on port 8080")
    app.run(host="0.0.0.0", port=8080)




