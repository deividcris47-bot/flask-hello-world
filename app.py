from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

# --- CONFIG ---
TOKEN = os.environ.get("WHATSAPP_TOKEN", "test")
PHONE_ID = os.environ.get("PHONE_ID", "test")

@app.route('/')
def home():
    return "Bot Deivid V8 - ONLINE - /test para probar", 200

@app.route('/test')
def test():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Sabado = 5
    if datetime.now().weekday() == 5:
        return f"Mercado cerrado sabado - {now} - Bot VIVO", 200
    return f"TEST OK V8 - Bot vivo - XAU - {now} - TODO BIEN", 200

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    verify_token = os.environ.get("VERIFY_TOKEN", "deivid123")
    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook_receive():
    data = request.get_json()
    print(f"Mensaje recibido: {data}")
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
