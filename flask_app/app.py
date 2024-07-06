from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__)

RASA_URL = "http://localhost:5005/webhooks/rest/webhook"


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message")

    if not message:
        return jsonify({"response": "No message received."})

    response = requests.post(RASA_URL, json={"sender": "user", "message": message})

    if response.status_code != 200:
        return jsonify({"response": "Failed to connect to Rasa server."})

    rasa_response = response.json()

    if not rasa_response:
        return jsonify({"response": "No response from Rasa."})

    response_text = rasa_response[0].get("text", "Sorry, I did not understand that.")
    prompt = rasa_response[0].get("buttons", None) or rasa_response[0].get(
        "buttons", []
    )

    if prompt:
        return jsonify({"response": response_text, "prompt": True})
    else:
        return jsonify({"response": response_text, "prompt": False})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
