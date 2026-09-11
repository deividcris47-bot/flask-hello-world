import os, time, requests, yfinance as yf
from flask import Flask
from threading import Thread

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

@app.route('/')
def home():
    return "BOT 5 SNIPER ACTIVO"

@app.route('/healthz')
def healthz():
    return "OK", 200

def enviar(texto):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": texto, "parse_mode": "Markdown"}
        r = requests.post(url, data=data, timeout=15)
        print(f"Telegram respuesta: {r.text}")
    except Exception as e:
        print(f"Error Telegram: {e}")

def bot_oro():
    print(">>> BOT 5 SNIPER INICIADO <<<", flush=True)
    time.sleep(5)
    enviar("✅ *Bot 5 SNIPER conectado - Test OK*")
    contador = 0
    while True:
        try:
            print("Chequeando oro...", flush=True)
            df = yf.download("GC=F", period="1d", interval="1m", progress=False)
            if df.empty:
                time.sleep(60); continue
            precio = float(df['Close'].iloc[-1])
            print(f"Precio actual: {precio}", flush=True)
            if 4508 <= precio <= 4525:
                contador += 1
                enviar(f"🎯 *SNIPER {contador}/5*\nSELL XAUUSD: `{precio:.2f}`\nSL: {precio+2.5:.2f}\nTP1: 4480\nTP2: 4366")
                time.sleep(3600)
        except Exception as e:
            print(f"Error bot: {e}", flush=True)
        time.sleep(60)

Thread(target=bot_oro, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
