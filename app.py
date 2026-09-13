from flask import Flask
import requests, os, time, threading, matplotlib.pyplot as plt, pandas as pd
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("8870473192:AAHLAqRgOKujQN4KT9xD1WIQHET-u7QywBU")
CHAT_ID = os.getenv("-1004419307514")
EC_TZ = pytz.timezone('America/Guayaquil')

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT BTC 1M Deivid LIVE"

def get_btc():
    try:
        r = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=60", timeout=15)
        data = r.json()
        df = pd.DataFrame(data)
        df = df[[1,2,3,4]].astype(float)
        df.columns = ['Open','High','Low','Close']
        return df
    except Exception as e:
        print(f"Error Binance: {e}")
        return None

def bot_loop():
    print(">>> BOT INICIADO - envio inmediato")
    time.sleep(3)
    while True:
        try:
            df = get_btc()
            if df is None:
                time.sleep(10)
                continue
            entrada = float(df['Close'].iloc[-1])
            
            plt.figure(figsize=(10,5))
            plt.plot(df['Close'], linewidth=1.5)
            plt.axhline(entrada, color='green', linestyle='--')
            plt.title(f"BTC 1M {datetime.now(EC_TZ).strftime('%H:%M:%S')} EC")
            plt.savefig('chart.png', dpi=100)
            plt.close()

            print(f"Enviando a {CHAT_ID}...")
            with open('chart.png','rb') as f:
                resp = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={'chat_id': CHAT_ID, 'caption': f"🟢 COMPRAR EN LINEA VERDE {entrada:.1f} - {datetime.now(EC_TZ).strftime('%H:%M')} EC"},
                    files={'photo': f},
                    timeout=20
                )
                print(f"Telegram resp: {resp.text}")
        except Exception as e:
            print(f"Error loop: {e}")
        time.sleep(900) # 15 minutos

threading.Thread(target=bot_loop, daemon=True).start()
