from flask import Flask
import os, requests

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT DEIVID ACTIVO - /enviar_grafico listo"

@app.route('/enviar_grafico')
def enviar_grafico():
    BOT_TOKEN = os.getenv("BOT_TOKEN","").strip()
    if not BOT_TOKEN:
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","").strip()
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID","").strip()
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": "PRUEBA DEIVID - SI VES ESTO YA FUNCIONA 🚀"}
    r = requests.post(url, data=data)
    return r.text
