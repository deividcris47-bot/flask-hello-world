import os, time, requests, yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "-1004419307514"

@app.route('/')
def home(): return "ORO BOS ON 24/7"
@app.route('/healthz')
def healthz(): return "OK", 200

def enviar(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def get_data():
    try:
        df = yf.download("GC=F", period="5d", interval="15m", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return None

def bot_loop():
    enviar("🚀 BOT ORO 24/7 INICIADO")
    ult = 0
    while True:
        try:
            df = get_data()
            if df is None: time.sleep(60); continue
            high_20 = df['High'].rolling(20).max().iloc[-2]
            low_20 = df['Low'].rolling(20).min().iloc[-2]
            precio = float(df['Close'].iloc[-1])
            if precio > high_20 and time.time()-ult > 3600:
                enviar(f"🟢 LONG ORO BOS\nPrecio {precio:.2f}\nSL {low_20:.2f}")
                ult = time.time()
            elif precio < low_20 and time.time()-ult > 3600:
                enviar(f"🔴 SHORT ORO CHoCH\nPrecio {precio:.2f}\nSL {high_20:.2f}")
                ult = time.time()
            time.sleep(120)
        except: time.sleep(60)

Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
