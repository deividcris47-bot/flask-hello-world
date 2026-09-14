import threading
import time
from flask import Flask
import requests # tu libreria para telegram

app = Flask(__name__)

# --- CONFIGURA AQUÍ ---
BOT_TOKEN = "TU_TOKEN_AQUI"
CHAT_ID = "TU_CHAT_ID"
# -----------------------

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def bot_loop():
    time.sleep(5)
    send_telegram("✅ PRUEBA OK - Tu bot 8/8 está conectado a Telegram. Ahora solo espera la señal real.")
    while True:
        try:
            # AQUÍ VA TU LOGICA 8/8 DEL ORO
            # if es_8_8_de_compra():
            #   send_telegram("SEÑAL REAL BUY 8/8...")
            print("Revisando XAUUSD 8/8...")
            time.sleep(60) # revisa cada 1 min
        except Exception as e:
            print(e)
            time.sleep(60)

# ESTA ES LA LINEA CLAVE QUE NO TENIAS
threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "Bot 8/8 Live - XAUUSD"

if __name__ == "__main__":
    app.run()
