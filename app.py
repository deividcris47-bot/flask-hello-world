import os, yfinance as yf, requests, threading, time
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def enviar(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        return True
    except: return False

def bot_loop():
    while True:
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home(): return "Bot 8/8 activo - Esperando señal 8/8"

@app.route('/test')
def test():
    ok = enviar("✅ PRUEBA OK - Tu bot 8/8 está conectado a Telegram. Ahora solo espera la señal real.")
    return f"Test enviado: {ok} | Token: {bool(BOT_TOKEN)} | Chat: {bool(CHAT_ID)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
