from flask import Flask
import requests, os, time, threading, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
EC_TZ = pytz.timezone('America/Guayaquil')

print(f"DEBUG ENV BOT_TOKEN existe: {bool(BOT_TOKEN)}")
print(f"DEBUG ENV CHAT_ID: {CHAT_ID}")

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT BTC 1M Deivid LIVE"

def bot_loop():
    print(">>> BOT INICIADO - envio inmediato", flush=True)
    time.sleep(5)
    while True:
        try:
            print(f"Intentando enviar a {CHAT_ID}...", flush=True)
            # Datos fake por ahora para probar Telegram, luego ponemos Binance
            plt.figure(figsize=(10,5))
            plt.plot([30000, 31000, 30500, 31500])
            plt.axhline(31500, color='green', linestyle='--')
            plt.title(f"TEST BTC {datetime.now(EC_TZ).strftime('%H:%M:%S')} EC")
            plt.savefig('chart.png', dpi=100)
            plt.close()

            with open('chart.png','rb') as f:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                data = {'chat_id': CHAT_ID, 'caption': f"🟢 PRUEBA - Si ves esto ya funciona {datetime.now(EC_TZ).strftime('%H:%M')}"}
                resp = requests.post(url, data=data, files={'photo': f}, timeout=20)
                print(f"Telegram resp: {resp.text}", flush=True)
        except Exception as e:
            print(f"Error loop: {e}", flush=True)
        time.sleep(60) # 1 min para prueba

threading.Thread(target=bot_loop, daemon=True).start()
