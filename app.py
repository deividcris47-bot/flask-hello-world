from flask import Flask
import requests, os, time, threading, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
EC_TZ = pytz.timezone('America/Guayaquil')

app = Flask(__name__)
@app.route('/')
def home(): return "BOT BTC 15M Deivid LIVE"

def get_btc_data():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=200"
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=['t','o','h','l','c','v','ct','qv','n','tb','tq','i'])
        df['c'] = df['c'].astype(float)
        return df
    except Exception as e:
        print(f"Error Binance: {e}")
        return None

def bot_loop():
    print(">>> BOT REAL BTC INICIADO", flush=True)
    time.sleep(10)
    while True:
        try:
            # Calcula proximo 15 min en hora Ecuador
            now_ec = datetime.now(EC_TZ)
            next_run = now_ec.replace(second=0, microsecond=0)
            minute = (now_ec.minute // 15 + 1) * 15
            if minute == 60:
                next_run = next_run.replace(minute=0) + timedelta(hours=1)
            else:
                next_run = next_run.replace(minute=minute)
            wait = (next_run - now_ec).total_seconds()
            print(f"Proximo envio: {next_run.strftime('%H:%M:%S')} EC - esperando {int(wait)}s", flush=True)
            if wait > 0: time.sleep(wait)

            df = get_btc_data()
            if df is None or df.empty:
                time.sleep(60)
                continue

            price = df['c'].iloc[-1]
            soporte = df['c'].tail(50).min()
            resistencia = df['c'].tail(50).max()

            plt.figure(figsize=(12,6))
            plt.plot(df['c'].values, color='#2E86DE', linewidth=1.5)
            plt.axhline(resistencia, color='red', linestyle='--', label=f'Resistencia {resistencia:.2f}')
            plt.axhline(soporte, color='green', linestyle='--', label=f'Soporte {soporte:.2f}')
            plt.title(f"BTC/USDT 1M - {now_ec.strftime('%Y-%m-%d %H:%M')} EC - Precio: ${price:.2f}")
            plt.legend()
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig('chart.png', dpi=150)
            plt.close()

            caption = f"📊 BTC/USDT 1M\n💰 Precio: ${price:.2f}\n🔴 Res: ${resistencia:.2f}\n🟢 Sop: ${soporte:.2f}\n🕐 {next_run.strftime('%H:%M')} EC (cada 15m)"

            with open('chart.png','rb') as f:
                url_tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                resp = requests.post(url_tg, data={'chat_id': CHAT_ID, 'caption': caption}, files={'photo': f}, timeout=20)
                print(f"Telegram resp: {resp.text[:200]}", flush=True)
        except Exception as e:
            print(f"Error loop real: {e}", flush=True)
            time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
