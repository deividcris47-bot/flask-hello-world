from flask import Flask
import threading, time, requests

app = Flask(__name__)

BOT_TOKEN = "PON_TU_TOKEN_AQUI"
CHAT_ID = "PON_TU_CHAT_ID"

def bot_loop():
    time.sleep(5)
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "✅ PRUEBA OK - Bot 8/8 conectado!"})
    except: pass
    while True:
        print("Revisando XAUUSD 8/8...", flush=True)
        time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "Bot 8/8 Live"

if __name__ == "__main__":
    app.run()
