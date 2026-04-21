from flask import Flask, request, jsonify, render_template, session
from groq import Groq
import os

app = Flask(__name__)
app.secret_key = "askredo-secret-2024"

# Groq API setup
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_INSTRUCTION = "তুমি একটি helpful AI assistant নাম AskRedo। তুমি বাংলা এবং ইংরেজি দুটো ভাষাতেই কথা বলতে পারো। ব্যবহারকারী যে ভাষায় কথা বলবে, তুমিও সেই ভাষায় উত্তর দেবে। সংক্ষিপ্ত, সহজবোধ্য এবং helpful উত্তর দেবে।"

FREE_LIMIT = 6969

@app.route("/")
def index():
    if "msg_count" not in session:
        session["msg_count"] = 0
    if "history" not in session:
        session["history"] = []
    return render_template("index.html", free_limit=FREE_LIMIT)

@app.route("/chat", methods=["POST"])
def chat():
    if "msg_count" not in session:
        session["msg_count"] = 0
    if "history" not in session:
        session["history"] = []

    if session["msg_count"] >= FREE_LIMIT:
        return jsonify({"error": "limit_reached"}), 403

    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "empty"}), 400

    try:
        # Build messages list for Groq
        messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]

        # Add history
        for msg in session["history"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Call Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content

        # Update session history
        session["history"] = session["history"] + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        session["msg_count"] = session["msg_count"] + 1
        session.modified = True

        return jsonify({
            "reply": reply,
            "used": session["msg_count"],
            "remaining": FREE_LIMIT - session["msg_count"]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)
