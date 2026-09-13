from flask import Flask
import requests, os, time, threading, matplotlib.pyplot as plt, pandas as pd
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("8870473192:AAElumHWfjg2paoljk1IANUvRW3dISms5eg")
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
        df = pd.DataFrame(data, columns=['t','O','H','L','C','v','ct','q','n','tb','tq','i'])
        df = df[[1,2,3,4]].astype(float)
        df.columns = ['Open','High','Low','Close']
        return df
    except Exception as e:
        print(f"Error Binance: {e}")
        return None

def bot_loop():
    print(">>> BOT INICIADO - esperando 15m")
    while True:
        try:
            df = get_btc()
            if df is None: 
                time.sleep(10)
                continue
            entrada = float(df['Close'].iloc[-1])
            
            # Grafico simple
            plt.figure(figsize=(10,6))
            plt.plot(df['Close'])
            plt.axhline(entrada, color='green')
            plt.savefig('chart.png')
            plt.close()

            if BOT_TOKEN and CHAT_ID:
                with open('chart.png','rb') as f:
                    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data={'chat_id': CHAT_ID, 'caption': f"🟢 COMPRAR EN LINEA VERDE {entrada:.1f} - {datetime.now(EC_TZ).strftime('%H:%M')} EC"}, files={'photo': f}, timeout=20)
                    print(f"Telegram resp: {resp.text}")
                    print(f"Enviado: COMPRAR EN LINEA VERDE {entrada}")
            else:
                print("FALTA BOT_TOKEN o CHAT_ID en Environment!")
        except Exception as e:
            print(f"Error loop: {e}")
        
        # Espera 15 min exactos
        time.sleep(900)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run()
